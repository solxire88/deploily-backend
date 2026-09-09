# -*- coding: utf-8 -*-

from flask import current_app
from flask_appbuilder.api import expose, protect
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_jwt_extended import current_user, jwt_required

from app import appbuilder, db
from app.core.celery_tasks.send_mail_task import send_mail
from app.core.controllers.subscription_controllers import SubscriptionModelApi
from app.core.models.mail_models import Mail
from app.services.mail_service import render_email
from app.service_deployment.models.deployment_service_subscription_model import (
    SubscriptionDeploymentService,
)
from app.utils.utils import get_user

deployment_columns = [
    "deployment_status",
    "required_restart",
    "access_url",
    "deployment_error",
    "custom_paramters",
    "argocd_url",
    "argocd_user_name",
    "argocd_password",
    "backend_url",
    "frontend_url",
    "pod_name_1",
    "pod_name_2",
    "pod_name_3",
    "pod_name_4",
    "pod_name_5",
    "pod_name_6",
    "pod_url_1",
    "pod_url_2",
    "pod_url_3",
    "pod_url_4",
    "pod_url_5",
    "pod_url_6",
]

edit_columns = [
    "deployment_status",
    "pod_name_1",
    "pod_name_2",
    "pod_name_3",
    "pod_name_4",
    "pod_name_5",
    "pod_name_6",
    "pod_url_1",
    "pod_url_2",
    "pod_url_3",
    "pod_url_4",
    "pod_url_5",
    "pod_url_6",
]


class DeploymentServiceSubscriptionModelApi(SubscriptionModelApi):
    resource_name = "deployment-service-subscription"
    datamodel = SQLAInterface(SubscriptionDeploymentService)

    add_columns = SubscriptionModelApi.add_columns + deployment_columns
    list_columns = SubscriptionModelApi.list_columns + deployment_columns
    show_columns = SubscriptionModelApi.show_columns + deployment_columns
    edit_columns = edit_columns

    @expose("/", methods=["GET"])
    @protect()  # or @jwt_required() depending on your setup
    @jwt_required()
    def get_list(self):
        """
        ---
        get:
          summary: Get active deployment Service Subscriptions
          description: >
            Returns a list of active (non-expired) deployment service subscriptions
            belonging to the current authenticated user.
          tags:
            - Deployment Service Subscription
          security:
            - BearerAuth: []   # JWT authentication
          responses:
            "200":
              description: Successful response with valid subscriptions
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      result:
                        type: array
                        items:
                          type: object
                          properties:
                            id:
                              type: integer
                              example: 12
                            name:
                              type: string
                              example: My Service
                            is_expired:
                              type: boolean
                              example: false
                            created_by:
                              type: string
                              example: user@test.com
            "401":
              description: Unauthorized (missing or invalid token)
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      message:
                        type: string
                        example: Unauthorized
        """
        user = get_user()
        if not user:
            return self.response(401, message="Unauthorized")

        # Load all subscriptions for the current user
        all_items = (
            self.datamodel.session.query(self.datamodel.obj).filter_by(created_by=user).all()
        )

        # Filter out expired items (computed property)
        valid_items = [item for item in all_items if not item.is_expired]

        # Convert to dict for JSON response
        result = [item.to_dict() for item in valid_items]

        return self.response(200, result=result)

    def post_update(self, item):
        user = current_user
        support_email = current_app.config.get("SUPPORT_EMAIL")

        # Check if a restart is required but hasn't been flagged yet
        if not item.required_restart and item.deployment_status in [
            "deployed",
            "error",
        ]:
            item.required_restart = True
            db.session.commit()

        if item.required_restart and item.deployment_status == "processing":
            # Prepare email body using template
            subject, email_body = render_email(
                "restart_application",
                user=user,
                application=item.service_plan.service.name,
                subscription_id=item.id,
            )

            # Create and persist the email record
            email = Mail(
                title=subject,
                body=email_body,
                email_to=support_email,
                email_from=support_email,
                mail_state="outGoing",
            )
            db.session.add(email)
            db.session.commit()

            # Send the email asynchronously
            send_mail.delay(email.id)

            print("### Email sent to:", support_email)

            user_subject, user_email_body = render_email(
                "user_restart_application",
                user=user,
                application=item.service_plan.service.name,
                subscription_id=item.id,
            )

            # Create and persist the email record
            email = Mail(
                title=user_subject,
                body=user_email_body,
                email_to=user.email,
                email_from=support_email,
                reply_to=support_email,
                mail_state="outGoing",
            )
            db.session.add(email)
            db.session.commit()

            # Send the email asynchronously
            send_mail.delay(email.id)

            print("### Email sent to:", support_email)

            item.required_restart = False
            db.session.commit()

        return super().post_update(item)


appbuilder.add_api(DeploymentServiceSubscriptionModelApi)
