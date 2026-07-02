from app import db
from app.core.models.plan_models import Plan
from app.core.models.service_plan_option_models import ServicePlanOption


def seed_service_plan_options():
    # Fetch plans
    basic = db.session.query(Plan).filter_by(name="Basic").first()
    pro = db.session.query(Plan).filter_by(name="Pro").first()

    options = [
        {
            "html_content": "1 CPU",
            "icon": "fa-microchip",
            "option_type": "cpu",
            "option_value": 40,
            "sequence": 1,
        },
        {
            "html_content": "2 GB RAM",
            "icon": "fa-memory",
            "option_type": "ram",
            "option_value": 40,
            "sequence": 2,
        },
        {
            "html_content": "10 GB Disk",
            "icon": "fa-hdd",
            "option_type": "disque",
            "option_value": 10,
            "sequence": 3,
        },
        {
            "html_content": "100 000 Requests / Month",
            "icon": "fa-arrows-rotate",  # or fa-gauge, fa-server
            "option_type": "request_limit",
            "option_value": 100000,
            "sequence": 4,
        },
    ]

    for opt in options:
        exists = (
            db.session.query(ServicePlanOption)
            .filter_by(
                html_content=opt["html_content"],
                option_type=opt["option_type"],
            )
            .first()
        )

        if exists:
            continue

        option = ServicePlanOption(
            html_content=opt["html_content"],
            icon=opt["icon"],
            option_type=opt["option_type"],
            option_value=opt["option_value"],
            sequence=opt["sequence"],
        )

        db.session.add(option)

    db.session.commit()
