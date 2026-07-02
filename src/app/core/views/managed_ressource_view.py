# -*- coding: utf-8 -*-

from flask_appbuilder import ModelView
from flask_appbuilder.models.sqla.filters import FilterEqual
from flask_appbuilder.models.sqla.interface import SQLAInterface
from markupsafe import Markup

from app import appbuilder, db
from app.core.models.managed_ressource_models import ManagedRessource


def _expired_tag_formatter(value):
    # `value` is the row's is_expired boolean
    if value:
        return Markup('<span class="label label-danger">Expired</span>')
    return Markup('<span class="label label-success">Active</span>')


_LIST_COLUMNS = [
    "id",
    "host_name",
    "byor",
    "start_date",
    "end_date",
    "monitoring",
    "provider_name",
    "is_expired",
]
_BASE_ORDER = ("id", "desc")
_LABEL_COLUMNS = {"is_expired": "Status"}
_FORMATTERS_COLUMNS = {"is_expired": _expired_tag_formatter}


class ManagedRessourcelView(ModelView):
    route_base = "/admin/managed-ressource"
    datamodel = SQLAInterface(ManagedRessource)
    list_columns = _LIST_COLUMNS + ["ressource_type"]
    base_order = _BASE_ORDER
    label_columns = _LABEL_COLUMNS
    formatters_columns = _FORMATTERS_COLUMNS


db.create_all()
appbuilder.add_view(
    ManagedRessourcelView,
    "Managed Ressources",
    icon="fa-solid fa-briefcase",
    category="Resources",
)


class VPSManagedRessourcelView(ModelView):
    route_base = "/admin/managed-ressource-vps"
    datamodel = SQLAInterface(ManagedRessource)
    list_columns = _LIST_COLUMNS + ["ip", "cd_agent", "gitops_tool", "backup_automation"]
    base_order = _BASE_ORDER
    label_columns = _LABEL_COLUMNS
    formatters_columns = _FORMATTERS_COLUMNS
    base_filters = [["ressource_type", FilterEqual, "vps"]]


db.create_all()
appbuilder.add_view(
    VPSManagedRessourcelView,
    "Managed Ressources - VPS",
    icon="fa-solid fa-briefcase",
    category="Resources",
)


class WebHostingManagedRessourcelView(ModelView):
    route_base = "/admin/managed-ressource-web-hosting"
    datamodel = SQLAInterface(ManagedRessource)
    list_columns = _LIST_COLUMNS + ["ip"]
    base_order = _BASE_ORDER
    label_columns = _LABEL_COLUMNS
    formatters_columns = _FORMATTERS_COLUMNS
    base_filters = [["ressource_type", FilterEqual, "web_hosting"]]


db.create_all()
appbuilder.add_view(
    WebHostingManagedRessourcelView,
    "Managed Ressources - Web Hosting",
    icon="fa-solid fa-briefcase",
    category="Resources",
)


class DNSManagedRessourcelView(ModelView):
    route_base = "/admin/managed-ressource-dns"
    datamodel = SQLAInterface(ManagedRessource)
    list_columns = _LIST_COLUMNS
    base_order = _BASE_ORDER
    label_columns = _LABEL_COLUMNS
    formatters_columns = _FORMATTERS_COLUMNS
    base_filters = [["ressource_type", FilterEqual, "dns"]]


db.create_all()
appbuilder.add_view(
    DNSManagedRessourcelView,
    "Managed Ressources - DNS",
    icon="fa-solid fa-briefcase",
    category="Resources",
)


class S3ManagedRessourcelView(ModelView):
    route_base = "/admin/managed-ressource-s3"
    datamodel = SQLAInterface(ManagedRessource)
    list_columns = _LIST_COLUMNS
    base_order = _BASE_ORDER
    label_columns = _LABEL_COLUMNS
    formatters_columns = _FORMATTERS_COLUMNS
    base_filters = [["ressource_type", FilterEqual, "s3"]]


db.create_all()
appbuilder.add_view(
    S3ManagedRessourcelView,
    "Managed Ressources - S3",
    icon="fa-solid fa-briefcase",
    category="Resources",
)


class EmailManagedRessourcelView(ModelView):
    route_base = "/admin/managed-ressource-email"
    datamodel = SQLAInterface(ManagedRessource)
    list_columns = _LIST_COLUMNS
    base_order = _BASE_ORDER
    label_columns = _LABEL_COLUMNS
    formatters_columns = _FORMATTERS_COLUMNS
    base_filters = [["ressource_type", FilterEqual, "email"]]


db.create_all()
appbuilder.add_view(
    EmailManagedRessourcelView,
    "Managed Ressources - Email",
    icon="fa-solid fa-briefcase",
    category="Resources",
)
