# src/seeders/plan_seeder.py
from app import db
from app.core.models.plan_models import Plan


def seed_plans():
    plans = [
        {"name": "Basic", "description": "Basic plan api"},
        {"name": "Pro", "description": "Pro plan api"},
        {"name": "Premium", "description": "Premium plan api"},
        {"name": "Basic odoo", "description": "Basic plan app"},
        {"name": "Pro odoo", "description": "Pro plan app"},
        {"name": "Premium odoo", "description": "Premium plan app"},
        {"name": "Basic VPS", "description": "Basic plan VPS"},
        {"name": "Pro VPS", "description": "Pro plan VPS"},
        {"name": "Premium VPS", "description": "Premium plan VPS"},
    ]

    for plan in plans:
        if not db.session.query(Plan).filter_by(name=plan["name"]).first():
            db.session.add(Plan(**plan))

    db.session.commit()
