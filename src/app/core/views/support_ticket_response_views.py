# -*- coding: utf-8 -*-

from flask import current_app, flash, redirect
from flask_appbuilder import ModelView, expose, has_access
from flask_appbuilder.models.sqla.interface import SQLAInterface

from app import appbuilder, db
from app.core.celery_tasks.send_mail_task import send_mail
from app.core.models.mail_models import Mail
from app.core.models.support_ticket_response_models import SupportTicketResponse
from app.services.mail_service import render_email


class SupportTicketResponseModelView(ModelView):
    route_base = "/admin/supportticket-response"
    datamodel = SQLAInterface(SupportTicketResponse)
    list_columns = [
        "created_by",
        "created_on",
        "support_ticket",
        "message_shortened",
        "status",
        "send_button",
    ]
    base_order = ("id", "desc")
    _exclude_columns = ["created_on"]
    add_exclude_columns = _exclude_columns
    edit_exclude_columns = _exclude_columns

    column_labels = {
        "send_button": "Action",
    }

    base_order = ("id", "desc")

    @expose("/<int:id>/send", methods=["POST"])
    @has_access
    def send(self, id):
        response = db.session.get(SupportTicketResponse, id)

        try:
            ticket = response
            user = ticket.support_ticket.created_by

            admin_subject, admin_body = render_email("support_ticket_response_admin", ticket=ticket)
            admin_email = Mail(
                title=admin_subject,
                body=admin_body,
                email_to=current_app.config["SUPPORT_EMAIL"],
                email_from=current_app.config["SUPPORT_EMAIL"],
                mail_state="outGoing",
            )

            db.session.add(admin_email)

            if user.email:
                print(f"User email: {user.email}")
                user_subject, user_body = render_email(
                    "support_ticket_response_user", ticket=ticket
                )

                user_email = Mail(
                    title=user_subject,
                    body=user_body,
                    email_to=user.email,
                    email_from=current_app.config["SUPPORT_EMAIL"],
                    reply_to=current_app.config["SUPPORT_EMAIL"],
                    mail_state="outGoing",
                )

                db.session.add(user_email)

            response.status = "sent"
            db.session.commit()
            send_mail.delay(admin_email.id)

            if user_email:
                send_mail.delay(user_email.id)

            flash("Response sent successfully", "success")

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error sending response {id}: {str(e)}")
            flash("Failed to send response", "danger")

        return redirect(self.get_redirect())


db.create_all()
appbuilder.add_view(
    SupportTicketResponseModelView,
    "Support Ticket Messages",
    icon="fa-solid fa-comments",
    category="Operations",
)
