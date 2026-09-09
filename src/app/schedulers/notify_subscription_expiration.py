import logging
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from flask import current_app as app

from app import app, db, scheduler
from app.core.models.subscription_models import Subscription
from app.services.mail_service import render_email, send_and_log_email

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sent_notifications = set()
last_reset_date = None  # Pour nettoyer le cache chaque jour


@scheduler.task("cron", id="notify_expiring_subscriptions", max_instances=1, hour=6, minute=0)
def notify_expiring_subscriptions():
    global sent_notifications, last_reset_date

    print(">>> [CRON] notify_expiring_subscriptions() running")
    today = datetime.now().date()

    if last_reset_date != today:
        sent_notifications.clear()
        last_reset_date = today
        print("[RESET] sent_notifications cleared for new day")

    try:
        # TODO when subscriotion is expired `status` should change to `inactive`
        with app.app_context():
            notice_days = [3, 5, 6, 7, 15, 30]

            subs = (
                db.session.query(Subscription)
                .filter(Subscription.status == "active", Subscription.start_date != None)
                .all()
            )

            for sub in subs:
                try:
                    end_date = (sub.start_date + relativedelta(months=sub.duration_month)).date()
                    days_difference = (end_date - today).days
                    if days_difference not in notice_days:
                        continue

                    key = (sub.id, days_difference, today)

                    if key in sent_notifications:
                        print(
                            f"[SKIP] Already sent for subscription {sub.id} at day {days_difference}"
                        )
                        continue

                    user = sub.created_by
                    expiration_date = sub.start_date + timedelta(days=30 * sub.duration_month)

                    print(
                        f"[NOTIFY] Subscription ID {sub.id} for user {user.username} expires in {days_difference} days."
                    )

                    subject, body = render_email(
                        "subscription_expiring",
                        user=user,
                        subscription=sub,
                        days=days_difference,
                        expiration_date=expiration_date.strftime("%Y-%m-%d"),
                    )

                    send_and_log_email(
                        user.email,
                        subject,
                        body,
                        from_email=app.config["NOTIFICATION_EMAIL"],
                        reply_to=app.config["NOTIFICATION_EMAIL"],
                    )

                    sent_notifications.add(key)

                except Exception as e:
                    logger.error(f"Error processing subscription {sub.id}: {e}")
                    continue

    except Exception as e:
        logger.error(f"Error in notify_expiring_subscriptions: {e}")
        raise
