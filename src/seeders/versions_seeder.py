# src/seeders/versions_seeder.py
from app import db
from app.service_apps.models.app_version_model import Version


def seed_versions():
    versions = [
        {"name": "18.0.0", "description": "odoo 18.0.0 release with new features and improvements"},
        {"name": "17.1.0", "description": "odoo 17.1.0 release with bug fixes and enhancements"},
        {"name": "16.0.0", "description": "odoo 16.0.0 release with new features and improvements"},
    ]

    for version in versions:
        if not db.session.query(Version).filter_by(name=version["name"]).first():
            db.session.add(Version(**version))

    db.session.commit()
