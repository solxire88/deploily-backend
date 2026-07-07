# -*- coding: utf-8 -*-

import logging

from flask import current_app, render_template, request
from flask_appbuilder.api import BaseApi, ModelRestApi, expose
from flask_appbuilder.models.sqla.interface import SQLAInterface

from app import appbuilder, db
from app.core.celery_tasks.send_mail_task import send_mail
from app.core.models.contact_us_models import ContactUs
from app.core.models.mail_models import Mail
from app.utils.utils import get_user

_logger = logging.getLogger(__name__)
_contact_us_display_columns = ["name", "email", "message", "phone", "service"]


class ContactUSModelApi(ModelRestApi):
    resource_name = "contact-us"
    base_order = ("id", "desc")
    datamodel = SQLAInterface(ContactUs)

    add_columns = ["name", "email", "message", "phone", "service"]

    list_columns = _contact_us_display_columns
    edit_columns = _contact_us_display_columns

    def pre_add(self, item: ContactUs):
        current_user = get_user()
        if current_user and current_user.is_authenticated:
            item.partner_id = current_user.id
            _logger.info(f"[ContactUs] Setting partner_id={current_user.id}")
        else:
            _logger.warning("[ContactUs] No authenticated user found")

    def post_add(self, item: ContactUs):
        """
        Called after a contact us is successfully created.
        """

        try:

            contact_us_template = render_template("emails/contact_us.html", item=item)

            email = Mail(
                title=f"New Contact US Created by {item.name}",
                body=contact_us_template,
                email_to=current_app.config["NOTIFICATION_EMAIL"],
                email_from=current_app.config["NOTIFICATION_EMAIL"],
                mail_state="outGoing",
            )

            db.session.add(email)
            db.session.commit()
            send_mail.delay(email.id)
            _logger.info(f"[EMAIL] Queued email for contact us {item.id}")

        except Exception as e:

            _logger.error(f"[EMAIL] Failed to create email for contact us {item.id}: {e}")


appbuilder.add_api(ContactUSModelApi)


class PublicContactUSModelApi(BaseApi):
    resource_name = "public"

    @expose("/contact-us", methods=["POST"])
    def add_contact_us(self):
        """
        Public Contact Us endpoint
        ---
        post:
          summary: Submit a contact us request
          description: Public endpoint to create a contact us record.
          requestBody:
            required: true
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    phone:
                      type: string
                      description: phone
                    service_id:
                      type: integer

                    email:
                      type: string
                      description: email
                    message:
                      type: string
                      description: message
                    name:
                      type: string
                      description: name
                    service_plan_id:
                      type: integer
                    ressource_plan_id:
                      type: integer
          responses:
            200:
              description: Contact created successfully
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      id:
                        type: integer
                      name:
                        type: string
            400:
              description: Bad request
            500:
              description: Internal server error
        """
        try:
            data = request.json
            _logger.info(f"Received contact us data: {data}")

            contact_us = ContactUs(
                email=data.get("email"),
                message=data.get("message"),
                name=data.get("name"),
                phone=data.get("phone"),
                service_id=data.get("service_id"),
                service_plan_id=data.get("service_plan_id"),
                ressource_plan_id=data.get("ressource_plan_id"),
            )
            db.session.add(contact_us)
            db.session.commit()

            # ✅ Return saved object fields properly
            return self.response(
                200,
                result={
                    "name": contact_us.name,
                    "message": contact_us.message,
                    "email": contact_us.email,
                    "phone": contact_us.phone,
                    "service_id": contact_us.service_id,
                    "service_plan_id": contact_us.service_plan_id,
                    "ressource_plan_id": contact_us.ressource_plan_id,
                },
            )

        except Exception as e:
            _logger.error(f"Error in add_contact_us: {e}", exc_info=True)
            db.session.rollback()
            return self.response_500(message="Internal Server Error")


appbuilder.add_api(PublicContactUSModelApi)
