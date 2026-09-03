# -*- coding: utf-8 -*-

import smtplib
from email.mime.text import MIMEText

from flask import current_app, render_template
from mjml import mjml2html

from app import db
from app.core.models import Mail
from app.core.models.email_template_model import EmailTemplate


# Templates whose original design used a receipt/table layout (green header,
# bordered detail table) instead of the standard branded card + footer.
_RECEIPT_STYLE_KEYS = {"payment_completed"}

# Internal/admin-facing notifications (email_to=NOTIFICATION_EMAIL or SUPPORT_EMAIL)
# are sent as plain HTML — no skeleton, no branding.
_PLAIN_KEYS = {
    "create_user",
    "contact_us",
    "support_ticket",
    "support_ticket_response_admin",
    "admin_support_ticket_closed",
    "admin_support_ticket_warning",
    "deploily_affiliation",
    "deploily_subscription",
    "deploily_subscription_trial",
    "restart_application",
}


def render_email(key, **context):
    tmpl = db.session.query(EmailTemplate).filter_by(key=key).first()
    if not tmpl:
        raise ValueError(f"No EmailTemplate found for key={key!r}")

    subject = current_app.jinja_env.from_string(tmpl.subject).render(**context)
    content_html = current_app.jinja_env.from_string(tmpl.body).render(**context)

    if key in _PLAIN_KEYS:
        return subject, content_html

    skeleton = "emails/_base_receipt.mjml" if key in _RECEIPT_STYLE_KEYS else "emails/_base.mjml"
    mjml_source = render_template(skeleton, content=content_html, **context)
    return subject, mjml2html(mjml_source)


def send_and_log_email(to, subject, body, from_email=None):
    mail = Mail(
        title=subject,
        email_from=from_email or current_app.config["MAIL_USERNAME"],
        email_to=to,
        body=body,
        mail_state="outGoing",
    )
    db.session.add(mail)
    db.session.flush()

    try:
        msg = MIMEText(body, "html")
        msg["Subject"] = subject
        msg["From"] = mail.email_from
        msg["To"] = mail.email_to

        smtp_host = current_app.config["MAIL_HOST"]
        smtp_port = int(current_app.config["MAIL_PORT"])
        smtp_user = current_app.config["MAIL_USERNAME"]
        smtp_pass = current_app.config["MAIL_PASSWORD"]

        server = smtplib.SMTP_SSL(host=smtp_host, port=smtp_port)
        server.set_debuglevel(1)
        server.login(smtp_user, smtp_pass)
        server.sendmail(msg["From"], [msg["To"]], msg.as_string())
        server.quit()

        mail.mail_state = "sent"
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Erreur envoi email à {to}: {e}")
        mail.mail_state = "error"

        db.session.commit()
    return mail
