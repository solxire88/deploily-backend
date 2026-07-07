# -*- coding: utf-8 -*-

from flask_appbuilder import ModelView
from flask_appbuilder.models.sqla.filters import FilterEqual, FilterNotEqual
from flask_appbuilder.models.sqla.interface import SQLAInterface

from app import appbuilder, db
from app.core.models.contact_us_models import ContactUs


class ContactUsModelView(ModelView):
    route_base = "/admin/contact-us"
    datamodel = SQLAInterface(ContactUs)
    list_columns = ["created_on", "name", "message", "phone", "contact_us_status"]
    base_order = ("id", "desc")
    add_form_query_rel_fields = {
        "ressource_plan": [["service_plan_type", FilterEqual, "ressource"]],
        "service_plan": [["service_plan_type", FilterNotEqual, "ressource"]],
    }
    edit_form_query_rel_fields = {
        "ressource_plan": [["service_plan_type", FilterEqual, "ressource"]],
        "service_plan": [["service_plan_type", FilterNotEqual, "ressource"]],
    }


db.create_all()
appbuilder.add_view(
    ContactUsModelView,
    "Contact Us ",
    icon="fa-solid fa-life-ring ",
    category="Operations",
)
