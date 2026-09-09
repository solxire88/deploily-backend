import json
import logging
import os
from datetime import datetime
from typing import Optional, Tuple

import requests
from dateutil.relativedelta import relativedelta
from flask import current_app
from slugify import slugify

from app.services.mail_service import render_email
from app.core.models import (
    ManagedRessource,
    Payment,
    PaymentProfile,
    ServicePlan,
    Subscription,
)
from app.core.models.mail_models import Mail
from app.services.payment_service import PaymentService
from app.services.subscription_api_service import ApiSubscriptionRequest
from app.services.subscription_mobile_application_service import (
    MobileApplicationDeploymentSubscriptionRequest,
)
from app.services.subscription_web_application_service import (
    WebApplicationDeploymentSubscriptionRequest,
)

_logger = logging.getLogger(__name__)


class SubscriptionServiceBase:

    def __init__(self, db_session, logger):
        self.db = db_session
        self.logger = logger

    def validate_profile(self, user, profile_id: int) -> Tuple[bool, str, Optional[object]]:
        """Validate user profile"""
        profile = self.db.query(PaymentProfile).filter_by(created_by=user, id=profile_id).first()

        if not profile:
            return False, "PaymentProfile not found", None

        if profile.balance is None:
            return False, "Insufficient balance", None

        return True, "", profile

    def validate_service_plan(self, plan_id: int, profile) -> Tuple[bool, str, Optional[object]]:
        """Validate service plan eligibility"""
        plan = self.db.query(ServicePlan).filter_by(id=plan_id).first()

        if not plan:
            return False, "Service Plan not found", None

        if profile.profile_type == "default" and plan.service and not plan.service.is_eligible:
            return False, "This service plan is not eligible for subscription", None

        return True, "", plan

    def validate_ressource_service_plan(
        self, ressource_service_plan_id: int
    ) -> Tuple[bool, str, Optional[object]]:
        """Validate ressource service plan"""
        ressource_service_plan = (
            self.db.query(ServicePlan).filter_by(id=ressource_service_plan_id).first()
        )

        if not ressource_service_plan:
            return False, "Ressource Service Plan not found", None

        return True, "", ressource_service_plan

    def validate_managed_ressource(
        self, managed_ressource_id: int
    ) -> Tuple[bool, str, Optional[object]]:
        """Validate managed ressource"""

        managed_ressource = (
            self.db.query(ManagedRessource).filter_by(id=managed_ressource_id).first()
        )

        if not managed_ressource:
            return False, "managed_ressource not found", None

        return True, "", managed_ressource

    def validate_version(self, version_id: int) -> Tuple[bool, str, Optional[object]]:
        """Validate version"""
        from app.service_apps.models.app_version_model import Version

        version = self.db.query(Version).filter_by(id=version_id).first()
        if not version:
            return self.response_400(message="Version not found")

        return True, "", version

    def verify_captcha(self, captcha_token: str) -> Tuple[bool, str]:
        """Verify Google reCAPTCHA token"""
        if not captcha_token:
            return False, "Missing CAPTCHA token"

        verify_url = "https://www.google.com/recaptcha/api/siteverify"
        payload = {
            "secret": current_app.config["CAPTCHA_SECRET_KEY"],
            "response": captcha_token,
        }

        try:
            response = requests.post(verify_url, data=payload, timeout=10)
            result = response.json()

            if not result.get("success"):
                return False, "CAPTCHA verification failed"

            return True, ""
        except Exception as e:
            self.logger.error(f"Failed to contact reCAPTCHA: {e}", exc_info=True)
            return False, "CAPTCHA verification error"

    def create_payment(
        self, price: float, payment_method: str, subscription_id: int, profile_id: int
    ) -> object:
        """Create payment record"""
        payment = Payment(
            amount=price,
            payment_method=payment_method,
            subscription_id=subscription_id,
            profile_id=profile_id,
            status="pending",
        )

        self.db.add(payment)
        self.db.flush()
        return payment

    def process_payment(
        self,
        invoice,
        total_amount: float,
        is_mvc_call,
        client_confirm_url,
        client_fail_url,
    ) -> Tuple[bool, str, dict]:
        """Process payment through external service"""
        # payment.order_id = "PAY" + str(payment.id)
        # self.db.commit()

        try:
            payment_service = PaymentService()
            payment_response = payment_service.post_payement(
                invoice.id,
                total_amount,
                is_mvc_call,
                client_confirm_url,
                client_fail_url,
            )[0]

            # Parse response if it's a string
            if isinstance(payment_response, str):
                try:
                    payment_response = json.loads(payment_response)
                except json.JSONDecodeError:
                    return False, "Invalid payment service response format", {}

            if not isinstance(payment_response, dict):
                return False, "Invalid payment service response", {}

            if "ERROR_CODE" in payment_response and payment_response["ERROR_CODE"] != "0":
                error_msg = payment_response.get("ERROR_MESSAGE", "Unknown error")
                return False, f"Payment failed: {error_msg}", {}

            # Update payment with external order ID
            invoice.satim_order_id = payment_response.get("ORDER_ID")
            self.db.commit()

            return True, "", payment_response

        except Exception as e:
            self.logger.error(f"Payment processing error: {e}", exc_info=True)
            return False, "Payment processing failed", {}

    def send_notification_emails(
        self, user, plan, total_amount: float, subscription, payment_method
    ):
        """Send notification emails to admin and user"""
        from app.core.celery_tasks.send_mail_task import send_mail

        is_trial = bool(getattr(subscription, "is_trial", False))

        # ------------------
        # ADMIN EMAIL
        # ------------------
        admin_template_key = "deploily_subscription_trial" if is_trial else "deploily_subscription"

        admin_title, admin_template = render_email(
            admin_template_key,
            user_name=user.username,
            plan=plan,
            subscription=subscription,
        )

        admin_email = Mail(
            title=admin_title,
            body=admin_template,
            email_to=current_app.config["NOTIFICATION_EMAIL"],
            email_from=current_app.config["NOTIFICATION_EMAIL"],
            mail_state="outGoing",
        )

        # ------------------
        # USER EMAIL
        # ------------------
        bank = agency = address = bank_account_number = None

        if payment_method == "bank_transfer" and not is_trial:
            bank = os.getenv("BANK", "")
            agency = os.getenv("AGENCY", "")
            address = os.getenv("ADDRESS", "")
            bank_account_number = os.getenv("BANK_ACCOUNT_NUMBER", "")

        user_template_key = "user_subscription_trial" if is_trial else "user_subscription"

        user_title, user_template = render_email(
            user_template_key,
            user=user,
            service_name=plan.service.name,
            plan_name=plan.plan.name,
            total_price=total_amount,
            payment_method=payment_method,
            subscription=subscription,
            bank=bank,
            agency=agency,
            address=address,
            bank_account_number=bank_account_number,
        )

        user_email = Mail(
            title=user_title,
            body=user_template,
            email_to=user.email,
            email_from=current_app.config["NOTIFICATION_EMAIL"],
            reply_to=current_app.config["NOTIFICATION_EMAIL"],
            mail_state="outGoing",
        )

        # ------------------
        # SAVE & SEND
        # ------------------
        self.db.add_all([admin_email, user_email])
        self.db.commit()

        send_mail.delay(admin_email.id)
        send_mail.delay(user_email.id)

        self.logger.info(
            f"Notification emails sent for {'trial ' if is_trial else ''}subscription {subscription.id}"
        )

    def update_old_subscription(
        self, old_subscription, is_renew: bool = False, is_upgrade: bool = False
    ):
        """Update old subscription after successful upgrade or renewal"""

        # Mark the subscription as expired by shifting the start date far in the past
        old_subscription.start_date = datetime.now() - relativedelta(
            months=old_subscription.duration_month + 1
        )
        # old_subscription.status = "inactive"

        # Set the correct flag
        if is_renew:
            old_subscription.is_renew = True
        if is_upgrade:
            old_subscription.is_upgrade = True

        self.db.commit()

    def create_managed_ressource(self, ressource_service_plan, subscription=None):
        """Create managed ressource record"""
        managed_ressource = ManagedRessource(
            ressource_service_plan_id=ressource_service_plan,
            ip="000.000.000.000",
            host_name=f"{slugify(subscription.profile.name)}-({subscription.id})",
            operating_system="Debian 12",
        )
        self.db.add(managed_ressource)
        self.db.flush()
        return managed_ressource

    def get_or_create_managed_ressource(self, ressource_plan, managed_ressource, subscription):
        # ! UNUSED
        """
        Assigns a managed ressource to the subscription.
        """
        _logger.info(f"🛠 Getting or creating managed ressource for subscription {subscription.id}")

        if ressource_plan is None and managed_ressource is None:
            return None

        user_id = subscription.created_by

        # Use provided managed_ressource if available
        if managed_ressource:
            subscription.managed_ressource_id = managed_ressource.id
            self.db.commit()
            _logger.info(f"✅ Used provided managed ressource ID: {managed_ressource.id}")
            return managed_ressource

        existing = (
            self.db.query(ManagedRessource)
            .join(Subscription, Subscription.managed_ressource_id == ManagedRessource.id)
            .filter(
                ManagedRessource.ressource_service_plan_id == ressource_plan.id,
                Subscription.created_by == user_id,
            )
            .first()
        )

        if existing:
            _logger.info(f"🔄 Found existing managed ressource ID: {existing.id}")
            subscription.managed_ressource_id = existing.id
            self.db.commit()
            return existing

        # Todo Create new managed ressource Manually
        new_managed = self.create_managed_ressource(
            ressource_service_plan=ressource_plan.id, subscription=subscription
        )
        subscription.managed_ressource_id = new_managed.id
        self.db.commit()
        _logger.info(f"🆕 Created new managed ressource ID: {new_managed.id}")
        return new_managed

    def get_date_diff_in_days(self, date1, date2):
        """
        Returns the number of full days between two dates.
        """
        if isinstance(date1, str):
            date1 = datetime.fromisoformat(date1)
        if isinstance(date2, str):
            date2 = datetime.fromisoformat(date2)

        d1_ms = date1.timestamp() * 1000  # milliseconds since epoch
        d2_ms = date2.timestamp() * 1000

        return (d2_ms - d1_ms) / (1000 * 60 * 60 * 24)  # exact float days

    def get_remaining_value(self, old_subscription):

        total_price = old_subscription.price
        start_date = old_subscription.start_date
        duration_month = old_subscription.duration_month

        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)

        end_date = start_date + relativedelta(months=duration_month)
        today = datetime.now()

        # If subscription expired
        if today >= end_date:
            return 0.0

        # If subscription hasn't started yet
        if today <= start_date:
            return round(total_price)

        remaining_days = self.get_date_diff_in_days(start_date, today)
        total_days = duration_month * 30  # Assuming each month has ~30 days
        remaining_value = ((total_days - remaining_days) * total_price) / total_days

        return round(remaining_value)

    def process_subscription_request(self, user, request_data) -> Tuple[bool, str, Optional[dict]]:

        # Validate profile
        is_valid, error_msg, profile = self.validate_profile(user, request_data.profile_id)
        if not is_valid:
            return False, error_msg, None

        # Validate service plan
        is_valid, error_msg, plan = self.validate_service_plan(
            request_data.service_plan_selected_id, profile
        )
        if not is_valid:
            return False, error_msg, None

        # Validate service plan
        ressource_plan = None
        if (
            type(request_data) != ApiSubscriptionRequest
            and request_data.ressource_service_plan_selected_id is not None
        ):
            is_valid, error_msg, ressource_plan = self.validate_ressource_service_plan(
                request_data.ressource_service_plan_selected_id
            )
            if not is_valid:
                return False, error_msg, None

        #  Validate managed ressource
        if type(request_data) == ApiSubscriptionRequest:
            managed_ressource = None
            provider_name = None
        elif request_data.managed_ressource_id is None or request_data.byor == None:
            managed_ressource = None
            provider_name = None

        else:
            is_valid, error_msg, managed_ressource = self.validate_managed_ressource(
                request_data.managed_ressource_id
            )
            provider_name = request_data.provider_name
            if not is_valid:
                return False, error_msg, None

        # Validate service plan
        if (
            type(request_data) == ApiSubscriptionRequest
            or type(request_data) == WebApplicationDeploymentSubscriptionRequest
            or type(request_data) == MobileApplicationDeploymentSubscriptionRequest
        ):
            version = None
        else:
            is_valid, error_msg, version = self.validate_version(request_data.version_selected_id)
            if not is_valid:
                return False, error_msg, None

            # Calculate pricing
        total_amount = plan.price * request_data.duration
        tva_rate = 0.0
        tva_amount = 0.0

        if ressource_plan:
            tva_rate = ressource_plan.tva_rate if ressource_plan.tva_rate else 0.0
            total_price_ressource = round(ressource_plan.price * request_data.duration)
            tva_amount = round((total_price_ressource * tva_rate) / 100, 2)
            tva_amount = tva_amount if tva_amount else 0.0

            total_amount += tva_amount + total_price_ressource

        final_price = total_amount

        # Determine subscription status based on balance
        has_sufficient_balance = profile.balance >= final_price
        subscription_status = "active" if has_sufficient_balance else "inactive"
        default_duration = current_app.config.get("DURATION_MONTHS", 3)
        subscription_json = {
            "plan": plan,
            "ressource_plan": ressource_plan if ressource_plan else None,
            "duration": request_data.duration,
            "duration": default_duration if plan.is_trial else request_data.duration,
            "total_amount": total_amount,
            "price": final_price,
            "profile": profile,
            "phone": request_data.phone,
            "provider_name": provider_name,
            "status": subscription_status,
            "version_id": version.id if version else None,
            "managed_ressource": managed_ressource if managed_ressource else None,
            "byor": request_data.byor if hasattr(request_data, "byor") else False,
            "is_trial": plan.is_trial if plan else False,
            "has_sufficient_balance": has_sufficient_balance,
            "tva_rate": tva_rate,
            "tva_amount": tva_amount,
        }
        return True, "success", subscription_json

    def handle_payment_process(self, user, subscription, request_data, has_sufficient_balance):
        """Handle payment processing logic."""

        satim_order_id = ""
        form_url = ""

        # Si l'utilisateur n'a PAS assez de solde → on déclenche le paiement
        if not has_sufficient_balance:
            payment = self.create_payment(
                price=subscription.total_amount,
                payment_method=request_data.payment_method,
                subscription_id=subscription.id,
                profile_id=subscription.profile_id,
            )

            # Paiement par carte pour profils non "default"
            if (
                request_data.payment_method == "card"
                and subscription.profile.profile_type != "default"
            ):
                # todo Vérification CAPTCHA
                # is_valid, error_msg = self.verify_captcha(request_data.captcha_token)
                # if not is_valid:
                #     return False, error_msg, None  # ❌ avant c'était response_400

                # Process paiement
                is_mvc_call = False
                client_confirm_url = request_data.client_confirm_url
                client_fail_url = request_data.client_fail_url

                success, error_msg, payment_response = self.process_payment(
                    subscription,
                    subscription.total_amount,
                    is_mvc_call,
                    client_confirm_url,
                    client_fail_url,
                )
                if not success:
                    return (
                        False,
                        error_msg,
                        None,
                    )  # ❌ idem, cohérent avec ton appel
                satim_order_id = payment_response.get("ORDER_ID", "")
                form_url = payment_response.get("FORM_URL", "")
                payment.satim_order_id = satim_order_id

                print(f"Order ID: {satim_order_id}, Form URL: {form_url}")
                self.db.commit()

            # Notifications
            self.send_notification_emails(
                user,
                subscription.service_plan,
                subscription.total_amount,
                subscription,
                request_data.payment_method,
            )

            # Commit transaction
            self.db.commit()

        return (
            True,
            "success",
            {
                "subscription": {
                    "id": subscription.id,
                    "name": subscription.name,
                    "start_date": subscription.start_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_amount": subscription.total_amount,
                    "price": subscription.price,
                    "status": subscription.status,
                    "duration_month": subscription.duration_month,
                    "service_plan_id": subscription.service_plan_id,
                },
                "order_id": satim_order_id,
                "form_url": form_url,
            },
        )
