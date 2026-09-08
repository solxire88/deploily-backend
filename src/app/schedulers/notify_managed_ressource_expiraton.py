from datetime import date, timedelta

from sqlalchemy import Date, cast

from app import app, db, scheduler
from app.core.models.managed_ressource_models import ManagedRessource
from app.services.mail_service import render_email, send_and_log_email

sent_ressource_notifications = set()
last_reset_date_ressource = None
notice_days = [1, 3, 7, 15, 30]


@scheduler.task("cron", id="notify_managed_ressource_expiration", max_instances=1, hour=7)
def notify_managed_ressource_expiration():
    global sent_ressource_notifications, last_reset_date_ressource

    today = date.today()
    # Reset daily sent cache
    if last_reset_date_ressource != today:
        sent_ressource_notifications.clear()
        last_reset_date_ressource = today

    try:
        with app.app_context():
            notice_dates = [today + timedelta(days=d) for d in notice_days]
            resources = (
                db.session.query(ManagedRessource)
                .filter(
                    ManagedRessource.byor == False,
                    ManagedRessource.end_date.isnot(None),
                    cast(ManagedRessource.end_date, Date).in_(notice_dates),
                )
                .all()
            )
            for res in resources:
                print(
                    f"Found resource expiring soon: {res.host_name} ({res.ip}) with end_date {res.end_date}"
                )
                try:

                    days_remaining = (res.end_date - today).days
                    key = (res.id, days_remaining, today)
                    if key in sent_ressource_notifications:
                        print(f"[SKIP] Already notified for resource {res.host_name} ({res.ip})")
                        continue

                    user = res.access_user
                    if not user:
                        print(f"[WARN] Resource {res.host_name} has no access_user assigned")
                        continue

                    print(
                        f"[NOTIFY] Resource {res.host_name} ({res.ip}) expires in {days_remaining} days for user {user.username}"
                    )

                    subject, body = render_email(
                        "managed_ressource_expiring",
                        user=user,
                        resource=res,
                        days=days_remaining,
                        expiration_date=res.end_date.strftime("%Y-%m-%d"),
                    )
                    send_and_log_email(user.email, subject, body)

                    admin_subject, admin_body = render_email(
                        "admin_resource_expiring_soon",
                        user=user,
                        res=res,
                        days=days_remaining,
                        expiration_date=res.end_date.strftime("%Y-%m-%d"),
                    )
                    send_and_log_email(app.config["NOTIFICATION_EMAIL"], admin_subject, admin_body)

                    sent_ressource_notifications.add(key)

                except Exception as e:
                    print(f"Error processing resource {res.id}: {e}")
                    continue

    except Exception as e:
        print(f"Error in notify_managed_ressource_expiration: {e}")
        raise
