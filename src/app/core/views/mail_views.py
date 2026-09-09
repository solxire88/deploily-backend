# -*- coding: utf-8 -*-

from flask_appbuilder import ModelView
from flask_appbuilder.models.sqla.interface import SQLAInterface

from app import appbuilder, db
from app.core.models.mail_models import Mail


class MailModelView(ModelView):
    route_base = "/admin/mail"
    datamodel = SQLAInterface(Mail)
    list_columns = ["created_on", "title", "email_from", "email_to", "reply_to", "mail_state"]
    base_order = ("id", "desc")


db.create_all()
appbuilder.add_view(
    MailModelView,
    "Mail ",
    icon="fa-solid fa-envelope-o",
    category="Operations",
)
