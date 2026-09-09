import logging
from datetime import date

from flask import current_app as app
from flask_appbuilder.security.sqla.models import User
from sqlalchemy import text

from app import app, db, scheduler
from app.core.models.support_ticket_models import SupportTicket
from app.core.models.support_ticket_response_models import SupportTicketResponse
from app.services.mail_service import render_email, send_and_log_email

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sent_notifications = set()
last_reset_date = None  # Pour nettoyer le cache chaque jour


def _last_sent_response(ticket: SupportTicket) -> SupportTicketResponse | None:
    """Return the most-recently *sent* response for this ticket, or None."""
    sent = [r for r in ticket.support_ticket_responses if r.status == "sent"]
    if not sent:
        return None
    return max(sent, key=lambda r: r.changed_on)


def _get_ticket_owner_email(ticket: SupportTicket) -> str | None:
    """Return the email of the customer who owns the ticket."""
    # AuditMixin stores the creator in `created_by` (a User relationship).
    user = getattr(ticket, "created_by", None)
    return getattr(user, "email", None) if user else None


def _customer_replied_after(ticket: SupportTicket, since: date) -> bool:
    """
    Return True if the customer added any response AFTER `since`.
    We detect a customer reply as a SupportTicketResponse whose `created_by`
    matches the ticket owner (i.e., not a Deploily team member).
    """
    owner = getattr(ticket, "created_by", None)
    if owner is None:
        return False
    for response in ticket.support_ticket_responses:
        creator = getattr(response, "created_by", None)
        if creator and creator.id == owner.id and response.created_on.date() > since:
            return True
    return False


def _get_system_user():
    """Return a system/bot user to attribute automated changes to."""
    return db.session.query(User).filter_by(username="admin").first()


@scheduler.task("cron", id="auto_close_support_tickets", max_instances=1, hour=5)
def auto_close_support_tickets() -> dict:
    """
    Run daily (e.g. via Celery beat).

    - Tickets open > 6 days since last team response with no customer reply
      → send warning email.
    - Tickets open > 7 days since last team response with no customer reply
      → close ticket + send closure email.
    """
    today = date.today()  # Use date to avoid timezone issues; we only care about days
    warned = 0
    closed = 0
    with scheduler.app.app_context():  # <-- wrap everything here

        open_tickets: list[SupportTicket] = (
            db.session.query(SupportTicket).filter(SupportTicket.status == "open").all()
        )
        system_user = _get_system_user()
        support_mail = app.config.get("SUPPORT_EMAIL")

        for ticket in open_tickets:
            last_response = _last_sent_response(ticket)
            if last_response is None:
                continue  # team hasn't replied yet — nothing to do

            response_date: date = last_response.changed_on.date()
            customer_email = _get_ticket_owner_email(ticket)
            if not customer_email:
                logger.warning("No email found for ticket #%s owner — skipping.", ticket.id)
                continue

            customer_replied = _customer_replied_after(ticket, since=response_date)
            if customer_replied:
                continue  # customer is engaged — leave ticket alone

            days_since_response = (today - response_date).days

            # ── Day 7+: close the ticket ──────────────────────────────────────────
            if days_since_response >= 7:

                db.session.execute(
                    text(
                        """
                        UPDATE support_ticket 
                        SET status = :status,
                            changed_on = :changed_on,
                            changed_by_fk = :user_id
                        WHERE id = :ticket_id
                    """
                    ),
                    {
                        "status": "closed",
                        "changed_on": today,
                        "user_id": system_user.id if system_user else None,
                        "ticket_id": ticket.id,
                    },
                )
                # _send_email(customer_email, CLOSURE_SUBJECT, CLOSURE_BODY, ticket)
                admin_subject, admin_body = render_email(
                    "admin_support_ticket_closed",
                    ticket=ticket,
                )
                send_and_log_email(support_mail, admin_subject, admin_body, from_email=support_mail)

                user_subject, user_body = render_email(
                    "user_support_ticket_closed",
                    ticket=ticket,
                )
                send_and_log_email(
                    customer_email,
                    user_subject,
                    user_body,
                    from_email=support_mail,
                    reply_to=support_mail,
                )

                closed += 1

            # ── Day 6: warn the customer ──────────────────────────────────────────
            elif days_since_response == 6:
                admin_subject, admin_body = render_email(
                    "admin_support_ticket_warning",
                    ticket=ticket,
                )
                send_and_log_email(support_mail, admin_subject, admin_body, from_email=support_mail)

                user_subject, user_body = render_email(
                    "user_support_ticket_warning",
                    ticket=ticket,
                )
                send_and_log_email(
                    customer_email,
                    user_subject,
                    user_body,
                    from_email=support_mail,
                    reply_to=support_mail,
                )
                warned += 1

            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                raise
        return {"warned": warned, "closed": closed}
