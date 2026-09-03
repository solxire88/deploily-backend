# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from flask import current_app
from flask_appbuilder import Model
from flask_appbuilder.models.mixins import AuditMixin, ImageColumn
from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, event
from sqlalchemy.orm import relationship

_logger = logging.getLogger(__name__)


class Payment(Model, AuditMixin):
    id = Column(Integer, primary_key=True)
    amount = Column(Float)
    status = Column(
        Enum("pending", "completed", "failed", name="status_payment"), default="pending"
    )
    start_date = Column(DateTime, default=lambda: datetime.now().replace(microsecond=0))
    payment_method = Column(
        Enum("card", "bank_transfer", "cloud_credit", name="payment_method_enum"),
        nullable=False,
    )
    profile_id = Column(Integer, ForeignKey("payment_profile.id"), nullable=False)
    profile = relationship("PaymentProfile")
    subscription_id = Column(Integer, ForeignKey("subscription.id"))
    subscription = relationship("Subscription", back_populates="payments", overlaps="payments")

    payment_receipt = Column(ImageColumn, nullable=True)
    satim_order_id = Column(String)
    order_id = Column(String)

    def __repr__(self):
        return f"{self.profile} [{self.amount}] / {self.start_date} / {self.status}"


@event.listens_for(Payment.status, "set")
def update_subscription_status(target, value, oldvalue, initiator):
    if oldvalue != value and value == "completed":
        if target.subscription:
            target.subscription.status = "active"
            target.subscription.payment_status = "paid"
    elif oldvalue != value and value == "failed":
        if target.subscription:
            target.subscription.status = "inactive"
            target.subscription.payment_status = "unpaid"

    return value


@event.listens_for(Payment, "after_update")
def payment_after_update(mapper, connection, target):
    """
    Triggered AFTER payment is updated.
    Sends email to admin only when status changes to 'completed'.
    Updates subscription status accordingly.
    """
    from sqlalchemy import inspect

    from app.core.models.mail_models import Mail
    from app.services.mail_service import render_email

    state = inspect(target)
    history = state.attrs.status.history

    if history.has_changes():
        from app.core.celery_tasks.send_mail_task import send_mail

        new_status = target.status

        if new_status == "completed":

            try:
                subject, body = render_email("payment_completed", item=target)
                result = connection.execute(
                    Mail.__table__.insert()
                    .returning(Mail.id)
                    .values(
                        title=subject,
                        body=body,
                        email_to=current_app.config["NOTIFICATION_EMAIL"],
                        email_from=current_app.config["NOTIFICATION_EMAIL"],
                        mail_state="outGoing",
                    )
                )

                email_id = result.scalar()
                print(f"Email record created with ID: {email_id}. Enqueuing email sending task.")
                send_mail.delay(email_id)

            except Exception:
                _logger.exception(
                    f"[EMAIL] Failed to send payment completed email for Payment #{target.id}"
                )

            except Exception:
                _logger.exception(
                    f"[EMAIL] Failed to send payment failed email for Payment #{target.id}"
                )
