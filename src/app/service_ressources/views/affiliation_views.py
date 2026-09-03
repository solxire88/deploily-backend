# -*- coding: utf-8 -*-
from flask import flash, redirect, url_for
from flask_appbuilder import ModelView, action
from flask_appbuilder.actions import action
from flask_appbuilder.models.sqla.interface import SQLAInterface

from app import appbuilder
from app.service_ressources.models.affiliation_model import Affiliation
from app.services.mail_service import render_email, send_and_log_email


class AffiliationView(ModelView):
    datamodel = SQLAInterface(Affiliation)
    route_base = "/admin/affiliation"

    list_columns = [
        "created_by",
        "provider",
        "service_plan",
        "created_on",
        "phone_number",
        "affiliation_state",
    ]
    base_order = ("id", "desc")
    _exclude_columns = ["created_on", "changed_on"]
    add_exclude_columns = _exclude_columns
    edit_exclude_columns = _exclude_columns

    @action(
        "validate_affiliation",
        "Valider",
        "Confirmer cette affiliation ?",
        "fa fa-check",
        single=True,
    )
    def validate_affiliation(self, affiliations):

        if not isinstance(affiliations, list):
            affiliations = [affiliations]
        validated_count = 0
        for affiliation in affiliations:
            if affiliation.affiliation_state != "pending":
                flash(
                    f"L'affiliation #{affiliation.id} est déjà validée ou non valide.",
                    "warning",
                )
                continue

            # Envoi de l'email au partenaire
            provider = affiliation.provider
            service_plan = affiliation.service_plan
            user = affiliation.created_by

            if provider and provider.mail_partnership:
                provider_subject, provider_email_body = render_email(
                    "provider_affiliation",
                    user=user,
                    provider=provider,
                    total_price=affiliation.total_price,
                    service_name=service_plan.service.name,
                    plan_name=service_plan.plan.name,
                )
                send_and_log_email(
                    to=provider.mail_partnership,
                    subject=provider_subject,
                    body=provider_email_body,
                )

            affiliation.affiliation_state = "confirmed"
            self.datamodel.edit(affiliation)
            validated_count += 1

        flash(
            f"{validated_count} affiliation(s) validée(s) et email(s) envoyé(s).",
            "success",
        )
        return redirect(url_for("AffiliationView.list"))


appbuilder.add_view(
    AffiliationView,
    "Affiliation",
    icon="fa-cart-arrow-down",
    category="Operations",
)
