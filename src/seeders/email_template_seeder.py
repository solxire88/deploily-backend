# src/seeders/email_template_seeder.py
import os

from flask_appbuilder.security.sqla.models import User

from app import db
from app.core.models.email_template_model import EmailTemplate

_EMAILS_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "templates", "emails")

# Subjects preserve the exact wording each call site hardcoded today, converted
# to Jinja strings using the same variable names each call site already passes.
_SUBJECTS = {
    "create_user": "New User Created {{ username }}",
    "payment_completed": "✅ New Payment Completed — {{ item.amount }}",
    "contact_us": "New Contact US Created by {{ item.name }}",
    "support_ticket": "New Support Ticket Created By {{ user.first_name }} {{ user.last_name }}",
    "support_ticket_user": "Your support ticket has been created successfully",
    "support_ticket_response_admin": "Support Ticket #{{ ticket.id }} - New Response",
    "support_ticket_response_user": "Your Support Ticket #{{ ticket.id }} Has a New Response",
    "admin_support_ticket_closed": "Your support ticket #{{ ticket.id }} has been closed",
    "user_support_ticket_closed": "Your support ticket #{{ ticket.id }} has been closed",
    "admin_support_ticket_warning": "Ticket #{{ ticket.id }} warning — no reply in 6 days",
    "user_support_ticket_warning": "Reminder: Your support ticket #{{ ticket.id }} is awaiting your response",
    "user_affiliation": "Nouvelle affiliation dans deploily.cloud",
    "deploily_affiliation": "New affiliation between the user {{ user.first_name }} and the provider {{ provider.name }}",
    "provider_affiliation": "Nouvelle affiliation via deploily.cloud",
    "user_application_deployed": "Your application has been deployed",
    "user_application_failed": "Your application has failed",
    "restart_application": "Your application is restarting, {{ user.username }}",
    "user_restart_application": "Your application is restarting, {{ user.username }}",
    "deploily_subscription": "New Subscription Created by {{ user_name }}",
    "deploily_subscription_trial": "New TRIAL Subscription Created by {{ user_name }}",
    "user_subscription": "Nouvelle souscription à deploily.cloud",
    "user_subscription_trial": "Votre période d’essai sur deploily.cloud a commencé",
    "subscription_expiring": "Your subscription will expire in {{ days }} days",
    "managed_ressource_expiring": "Managed Resource Subscription Expiring in {{ days }} Days",
}


def seed_email_templates():
    # AuditMixin's created_by_fk/changed_by_fk are NOT NULL, normally filled in
    # from the logged-in user on a real request — a CLI seed run has none, so
    # attribute seeded rows to the admin user, same as support_ticket_tasks.py's
    # _get_system_user().
    system_user = db.session.query(User).filter_by(username="admin").first()
    if not system_user:
        raise RuntimeError(
            "No 'admin' user found — run `flask fab create-admin` before seeding email templates."
        )

    for key, subject in _SUBJECTS.items():
        if db.session.query(EmailTemplate).filter_by(key=key).first():
            continue

        file_path = os.path.join(_EMAILS_DIR, f"{key}.html")
        with open(file_path, "r", encoding="utf-8") as f:
            body = f.read()

        db.session.add(
            EmailTemplate(
                key=key,
                subject=subject,
                body=body,
                created_by_fk=system_user.id,
                changed_by_fk=system_user.id,
            )
        )

    db.session.commit()
