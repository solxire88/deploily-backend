# -*- coding: utf-8 -*-
from app import db
from app.service_api.models.api_services_model import ApiService
from app.service_apps.models.app_version_model import Version
from app.service_apps.models.apps_services_model import AppService
from app.service_ressources.models.services_ressources_model import (  # adjust import path
    RessourceService,
)


def seed_api_services():
    version = db.session.query(Version).filter_by(name="18.0.0").first()
    print(f"Found version: {version}")  # Debugging line
    api_services = [
        {
            "name": "Open meteo API",
            "apisix_group_id": "open-meteo",
            "short_description": "Real-time weather data access.",
            "description": "Provides current and forecasted weather data via REST endpoints.",
            "documentation_url": "#",
            "unit_price": 9.99,
            "is_published": True,
            "is_eligible": True,
            "price_category": "monthly",
            "service_slug": "open-meteo",
        },
    ]
    ressource_services = [
        {
            "name": "VPS",
            "short_description": "Virtual Private Server.",
            "description": "A virtualized server environment for hosting applications and services.",
            "documentation_url": "#",
            "unit_price": 9.99,
            "is_published": True,
            "is_eligible": True,
            "price_category": "monthly",
        },
    ]
    app_services = [
        {
            "name": "Odoo ERP",
            "description": "Comprehensive business management software.",
            "short_description": "Manage your business operations efficiently.",
            "documentation_url": "#",
            "unit_price": 29.99,
            "is_published": True,
            "is_eligible": True,
            "price_category": "monthly",
            "minimal_cpu": 2,
            "minimal_ram": 4,
            "minimal_disk": 20,
            "demo_url": "#",
            "service_slug": "odoo-erp",
            "app_versions": [version] if version else [],
        },
    ]

    for data in api_services:
        exists = db.session.query(ApiService).filter_by(name=data["name"]).first()
        if exists:
            print(f"Skipped existing ApiService: {data['name']}")
            continue

        service = ApiService(**data)
        db.session.add(service)
        print(f"Added ApiService: {data['name']}")

    db.session.commit()
    print("API services seeded.")

    for data in ressource_services:
        exists = db.session.query(RessourceService).filter_by(name=data["name"]).first()
        if exists:
            print(f"Skipped existing RessourceService: {data['name']}")
            continue

        service = RessourceService(**data)
        db.session.add(service)
        print(f"Added RessourceService: {data['name']}")

    db.session.commit()
    print("Ressource services seeded.")

    for data in app_services:
        exists = db.session.query(AppService).filter_by(name=data["name"]).first()
        if exists:
            print(f"Skipped existing AppService: {data['name']}")
            continue

        service = AppService(**data)
        db.session.add(service)
        print(f"Added AppService: {data['name']}")

    db.session.commit()
    print("API services seeded.")
