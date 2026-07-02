# -*- coding: utf-8 -*-
from app import db
from app.core.models.plan_models import Plan
from app.core.models.service_plan_models import ServicePlan
from app.core.models.service_plan_option_models import ServicePlanOption
from app.service_api.models.api_services_model import ApiService  # adjust import path
from app.service_apps.models.apps_services_model import AppService  # adjust import path
from app.service_ressources.models.services_ressources_model import (  # adjust import path
    RessourceService,
)


def seed_service_plans():
    basic = db.session.query(Plan).filter_by(name="Basic").first()
    pro = db.session.query(Plan).filter_by(name="Pro").first()
    basic_odoo = db.session.query(Plan).filter_by(name="Basic odoo").first()
    pro_odoo = db.session.query(Plan).filter_by(name="Pro odoo").first()
    basic_ressource = db.session.query(Plan).filter_by(name="Basic VPS").first()

    service_weather = db.session.query(ApiService).filter_by(apisix_group_id="open-meteo").first()
    service_odoo = db.session.query(AppService).filter_by(name="Odoo ERP").first()
    service_ressource = db.session.query(RessourceService).filter_by(name="VPS").first()

    if not service_weather or not service_odoo or not service_ressource:
        raise RuntimeError("No Service found — seed Service table first.")

    if not basic or not pro or not basic_odoo or not pro_odoo or not basic_ressource:
        raise RuntimeError("Plans not found — run seed_plans() first.")

    cpu = db.session.query(ServicePlanOption).filter_by(option_type="cpu").first()
    ram = db.session.query(ServicePlanOption).filter_by(option_type="ram").first()
    disk = db.session.query(ServicePlanOption).filter_by(option_type="disque").first()

    # NOTE: option_value is stored as an int in the seeder above (100000, not "100000").
    # Filtering with a string here silently returns None on most DBs (esp. Postgres).
    request_limit = (
        db.session.query(ServicePlanOption)
        .filter_by(option_type="request_limit", option_value=100000)
        .first()
    )

    # Debug visibility — remove once confirmed working
    print("cpu:", cpu)
    print("ram:", ram)
    print("disk:", disk)
    print("request_limit:", request_limit)

    service_plans = [
        {
            "price": 1000.0,
            "preparation_time": 24,
            "tva_rate": 0.0,
            "plan": basic,
            "is_trial": True,
            "subscription_category": "monthly",
            "service_plan_type": "api",
            "is_published": True,
            "display_on_app": True,
            "priority": 1,
            "options": [request_limit],
            "service": service_weather,
        },
        {
            "price": 1900.99,
            "preparation_time": 24,
            "tva_rate": 0.0,
            "plan": pro,
            "is_trial": False,
            "subscription_category": "monthly",
            "service_plan_type": "api",
            "is_published": True,
            "display_on_app": True,
            "priority": 2,
            "options": [request_limit],
            "service": service_weather,
        },
        {
            "price": 1000.0,
            "preparation_time": 24,
            "tva_rate": 0.0,
            "plan": basic_odoo,
            "is_trial": True,
            "subscription_category": "monthly",
            "service_plan_type": "app",
            "is_published": True,
            "display_on_app": True,
            "priority": 1,
            "options": [cpu, ram, disk],
            "service": service_odoo,
        },
        {
            "price": 1900.99,
            "preparation_time": 24,
            "tva_rate": 0.0,
            "plan": basic_ressource,
            "is_trial": False,
            "subscription_category": "monthly",
            "service_plan_type": "ressource",
            "is_published": True,
            "display_on_app": True,
            "priority": 2,
            "options": [cpu, ram, disk],
            "service": service_ressource,
        },
    ]

    for sp in service_plans:
        options = sp.pop("options")
        options = [opt for opt in options if opt]  # drop any None lookups

        existing = (
            db.session.query(ServicePlan).filter_by(service=sp["service"], plan=sp["plan"]).first()
        )

        if existing:
            # Row already exists — previously this just `continue`d and left
            # options empty forever. Now we sync missing options onto it.
            added_any = False
            for opt in options:
                if opt not in existing.options:
                    existing.options.append(opt)
                    added_any = True
            if added_any:
                print(f"Updated options on existing ServicePlan (plan={sp['plan'].name}).")
            else:
                print(f"ServicePlan already up to date (plan={sp['plan'].name}).")
            continue

        instance = ServicePlan(**sp)
        for opt in options:
            instance.options.append(opt)

        db.session.add(instance)
        print(f"Added ServicePlan (plan={sp['plan'].name}) with {len(options)} option(s).")

    db.session.commit()
    print("Service plans seeded.")
