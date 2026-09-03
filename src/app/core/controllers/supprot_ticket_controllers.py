import logging
import os

from flask import current_app, jsonify, request
from flask_appbuilder.api import ModelRestApi, expose, protect
from flask_appbuilder.models.sqla.filters import FilterEqualFunction
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_jwt_extended import current_user, jwt_required

from app import appbuilder, db
from app.core.celery_tasks.send_mail_task import send_mail
from app.core.models.mail_models import Mail
from app.core.models.support_ticket_models import SupportTicket
from app.services.mail_service import render_email
from app.utils.utils import get_user, process_and_save_image

_logger = logging.getLogger(__name__)

_support_ticket_display_columns = [
    "id",
    "title",
    "status",
    "description",
    "image",
    "subscription_id",
    "subscription",
    "created_on",
    "responses_with_details",
    "created_by_fk",
]


class SupportTicketModelApi(ModelRestApi):
    resource_name = "support-ticket"
    base_order = ("id", "desc")
    datamodel = SQLAInterface(SupportTicket)
    base_filters = [["created_by", FilterEqualFunction, get_user]]
    add_columns = [
        "id",
        "title",
        "status",
        "description",
        "image",
        "subscription_id",
        "subscription",
        "support_ticket_responses",
    ]
    list_columns = _support_ticket_display_columns
    edit_columns = [
        "title",
        "status",
        "description",
    ]
    show_columns = _support_ticket_display_columns
    _exclude_columns = [
        "changed_on",
        "created_by",
        "changed_by",
    ]

    def post_add(self, item: SupportTicket):
        """
        Called after a support ticket is successfully created.
        """
        try:
            user = current_user
            subject, support_tickert_template = render_email(
                "support_ticket", item=item, user=user
            )

            email = Mail(
                title=subject,
                body=support_tickert_template,
                email_to=current_app.config["SUPPORT_EMAIL"],  # ✅ SUPPORT TEAM EMAIL
                email_from=current_app.config["SUPPORT_EMAIL"],
                mail_state="outGoing",
            )
            db.session.add(email)
            if user.email:
                user_subject, user_template = render_email(
                    "support_ticket_user",
                    item=item,
                    user=user,
                )

                user_email = Mail(
                    title=user_subject,
                    body=user_template,
                    email_to=user.email,  # ✅ USER EMAIL
                    email_from=current_app.config["SUPPORT_EMAIL"],
                    mail_state="outGoing",
                )

                db.session.add(user_email)

            db.session.commit()
            send_mail.delay(email.id)
            if user.email:
                send_mail.delay(user_email.id)
            _logger.info(f"[EMAIL] Support ticket {item.id} emails queued (admin + user)")
        except Exception as e:
            _logger.error(f"[EMAIL] Failed to create email for support ticket {item.id}: {e}")

    @expose("/<int:support_ticket_id>/upload-image", methods=["PATCH"])
    @protect()
    @jwt_required()
    def upload_image(self, support_ticket_id):
        """
        Upload or replace ONE image for a support ticket
        ---
        patch:
            summary: Upload support ticket image
            description: Upload or replace a single image for a support ticket.
            tags:
                - Support Ticket
            parameters:
              - in: path
                name: support_ticket_id
                required: true
                schema:
                    type: integer
                description: ID of the support ticket
            requestBody:
                required: true
                content:
                    multipart/form-data:
                        schema:
                            type: object
                            required:
                                - file
                            properties:
                                file:
                                    type: string
                                    format: binary
                                    description: Image file to upload
                            encoding:
                                file:
                                    contentType: image/*
            responses:
                '200':
                    description: Image uploaded successfully
                    content:
                        application/json:
                            schema:
                                type: object
                                properties:
                                    message:
                                        type: string
                                        example: Image uploaded successfully
                                    ticket_id:
                                        type: integer
                                        example: 12
                                    image:
                                        type: string
                                        example: support_ticket_12.jpg
                '400':
                    description: No valid image provided
                '404':
                    description: Support ticket not found
                '500':
                    description: Image upload failed
        """
        file = request.files.get("file")

        if not file or not file.filename or file.filename.lower() == "blob":
            return jsonify({"error": "No valid image provided"}), 400

        upload_folder = appbuilder.get_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_folder, exist_ok=True)

        ticket = (
            db.session.query(SupportTicket).filter(SupportTicket.id == support_ticket_id).first()
        )

        if not ticket:
            return jsonify({"error": "Support ticket not found"}), 404

        try:
            if ticket.image:
                old_path = os.path.join(upload_folder, ticket.image)
                if os.path.exists(old_path):
                    os.remove(old_path)

            saved_filename = process_and_save_image(file, upload_folder)

            ticket.image = saved_filename
            db.session.commit()

            return (
                jsonify(
                    {
                        "message": "Image uploaded successfully",
                        "ticket_id": ticket.id,
                        "image": saved_filename,
                    }
                ),
                200,
            )

        except Exception as e:
            return jsonify({"error": str(e)}), 500


appbuilder.add_api(SupportTicketModelApi)
