# -*- coding: utf-8 -*-

from flask import current_app
from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String, Text, event
from sqlalchemy.orm import Session as SASession
from sqlalchemy.orm import object_session, relationship

from app import db
from app.core.models import Subscription
from app.core.models.mail_models import Mail
from app.services.mail_service import render_email


class SubscriptionAppService(Subscription):
    __tablename__ = "subscription_app_service"
    id = Column(Integer, ForeignKey("subscription.id"), primary_key=True)
    __mapper_args__ = {
        "polymorphic_identity": "subscription_app_service",
    }
    type = Column(String(50), default="subscription_app_service", nullable=False)

    application_status = Column(
        Enum("processing", "deployed", "error", name="application_status"),
        default="processing",
    )
    required_restart = Column(Boolean, default=False)
    access_url = Column(String(100))
    deployment_error = Column("error", Text())

    version_id = Column(Integer, ForeignKey("version.id"))
    version = relationship("Version", back_populates="app_subscriptions")
    console_url = Column(String(50))
    demo_url = Column(String(255), nullable=True)
    internal_note = Column(Text, nullable=True)
    ressource_service_plan_id = Column(Integer, ForeignKey("service_plan.id"))
    ressource_service_plan = relationship("ServicePlan")
    is_trial = Column(Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "is_expired": self.is_expired,
            # "short_description": self.short_description,
            # "price_period": self.price_period,
            "name": self.name,
            # "image_service": self.image_service,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "total_amount": self.total_amount,
            "price": self.price,
            # "is_in_favorite": self.is_in_favorite,
            "application_status": self.application_status,
            "payment_status": self.payment_status,
            "duration_month": self.duration_month,
            "status": self.status,
            "service_plan_id": self.service_plan.id if self.service_plan else None,
            "service_plan": {
                "id": self.service_plan.id,
                "price": self.service_plan.price,
                "subscription_category": self.service_plan.subscription_category,
            },
            "promo_code_id": self.promo_code.id if self.promo_code else None,
            "promo_code_name": self.promo_code.code if self.promo_code else None,
            "api_key": self.api_key,
            "is_encrypted": self.is_encrypted,
            "profile_id": self.profile.id if self.profile else None,
            "profile_name": self.profile.name if hasattr(self.profile, "name") else None,
            "is_upgrade": self.is_upgrade,
            "is_renew": self.is_renew,
            "is_expired": self.is_expired,
            "service_details": {
                "id": self.service_details.get("id"),
                "name": self.service_details.get("name"),
                "description": self.service_details.get("description"),
                "documentation_url": self.service_details.get("documentation_url"),
                "api_playground_url": self.service_details.get("api_playground_url"),
                "unit_price": self.service_details.get("unit_price"),
                "price_period": self.service_details.get("price_period"),
                "service_url": self.service_details.get("service_url"),
                "image_service": self.service_details.get("image_service"),
                "short_description": self.service_details.get("short_description"),
                "specifications": self.service_details.get("specifications"),
                "curl_command": self.service_details.get("curl_command"),
                "api_key": self.service_details.get("api_key"),
                "is_subscribed": self.service_details.get("is_subscribed"),
                "service_slug": self.service_details.get("service_slug"),
                "monitoring": self.service_details.get("monitoring"),
                "ssh_access": self.service_details.get("ssh_access"),
                "type": self.service_details.get("type"),
            },
            "managed_ressource_details": {
                "id": self.managed_ressource_details.get("id"),
                "display_on_app": self.managed_ressource_details.get("display_on_app"),
                "is_custom": self.managed_ressource_details.get("is_custom"),
                "is_published": self.managed_ressource_details.get("is_published"),
                "plan_id": self.managed_ressource_details.get("plan_id"),
                "preparation_time": self.managed_ressource_details.get("preparation_time"),
                "price": self.managed_ressource_details.get("price"),
                "priority": self.managed_ressource_details.get("priority"),
                "service_id": self.managed_ressource_details.get("service_id"),
                "service_plan_type": self.managed_ressource_details.get("service_plan_type"),
                "subscription_category": self.managed_ressource_details.get(
                    "subscription_category"
                ),
            },
        }


_pending_deployed_apps = {}


@event.listens_for(SubscriptionAppService, "after_update")
def mark_for_email(mapper, connection, target):

    if target.application_status in ["deployed", "error"]:
        session = object_session(target)
        if session:
            session_id = id(session)
            _pending_deployed_apps.setdefault(session_id, []).append(target)


@event.listens_for(db.session.__class__, "after_commit")
def send_deployed_app_emails(session):
    from app.core.celery_tasks.send_mail_task import send_mail

    session_id = id(session)
    targets = _pending_deployed_apps.pop(session_id, [])

    if not targets:
        return

    # Use a new session for email creation
    new_session = SASession(bind=db.engine)
    notify_email = current_app.config.get("NOTIFICATION_EMAIL")

    try:
        for target in targets:
            # Skip if user email is missing
            if not getattr(target.created_by, "email", None):
                print(f"[WARN] User {target.created_by.id} has no email.")
                continue

            if target.application_status == "deployed":
                template_key = "user_application_deployed"
                message = ""
            else:
                template_key = "user_application_failed"
                message = target.deployment_error

            # Render email body
            title, user_body = render_email(
                template_key, user=target.created_by, application=target.name, message=message
            )

            # Create Mail object
            user_email = Mail(
                title=title,
                body=user_body,
                email_to=target.created_by.email,
                email_from=notify_email,
                mail_state="outGoing",
            )

            new_session.add(user_email)
            new_session.flush()  # Assign ID
            email_id = user_email.id

            new_session.commit()  # Commit before sending
            send_mail.delay(email_id)  # Queue for sending

    except Exception as e:
        new_session.rollback()
        print(f"[Email Send Error] {e}")

    finally:
        new_session.close()
