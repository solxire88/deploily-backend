# -*- coding: utf-8 -*-

from collections import OrderedDict
from datetime import datetime, timedelta

from flask_appbuilder import IndexView, expose
from flask_login import current_user

_MONTHS_BACK = 6


def _is_admin():
    return current_user.is_authenticated and any(
        role.name == "Admin" for role in current_user.roles
    )


def _kpis(db, Subscription, SupportTicket, Affiliation, User):
    return {
        "active_subscriptions": db.session.query(Subscription)
        .filter(Subscription.status == "active")
        .count(),
        "open_tickets": db.session.query(SupportTicket)
        .filter(SupportTicket.status == "open")
        .count(),
        "pending_affiliations": db.session.query(Affiliation)
        .filter(Affiliation.affiliation_state == "pending")
        .count(),
        "total_users": db.session.query(User).count(),
    }


def _group_counts(db, func, column):
    rows = db.session.query(column, func.count()).group_by(column).all()
    return {str(label) if label is not None else "unknown": count for label, count in rows}


def _signups_per_month(db, User):
    since = datetime.now() - timedelta(days=30 * _MONTHS_BACK)
    users = (
        db.session.query(User.created_on)
        .filter(User.created_on.isnot(None), User.created_on >= since)
        .all()
    )

    buckets = OrderedDict()
    cursor = since.replace(day=1)
    for _ in range(_MONTHS_BACK + 1):
        buckets[cursor.strftime("%Y-%m")] = 0
        cursor = (cursor + timedelta(days=32)).replace(day=1)

    for (created_on,) in users:
        key = created_on.strftime("%Y-%m")
        if key in buckets:
            buckets[key] += 1

    return buckets


def _expiring_subscriptions(db, func, Subscription, days=7):
    now = datetime.now()
    horizon = now + timedelta(days=days)
    expiry_date = func.make_interval(0, Subscription.duration_month) + Subscription.start_date

    return (
        db.session.query(Subscription)
        .filter(Subscription.status == "active", expiry_date >= now, expiry_date <= horizon)
        .order_by(expiry_date.asc())
        .limit(5)
        .all()
    )


def _latest_open_tickets(db, SupportTicket):
    return (
        db.session.query(SupportTicket)
        .filter(SupportTicket.status == "open")
        .order_by(SupportTicket.created_on.desc())
        .limit(5)
        .all()
    )


def _latest_signups(db, User):
    return db.session.query(User).order_by(User.created_on.desc()).limit(5).all()


def _pending_affiliations(db, Affiliation):
    return (
        db.session.query(Affiliation)
        .filter(Affiliation.affiliation_state == "pending")
        .order_by(Affiliation.created_on.desc())
        .limit(5)
        .all()
    )


def build_dashboard_context():
    # Imported lazily: this module is imported before models/db finish wiring
    # up during app init (AdminDashboardIndexView must exist before
    # AppBuilder() is constructed), so these can't be top-level imports.
    from sqlalchemy import func

    from app import db
    from app.core.models.subscription_models import Subscription
    from app.core.models.support_ticket_models import SupportTicket
    from app.service_ressources.models.affiliation_model import Affiliation
    from flask_appbuilder.security.sqla.models import User

    return {
        "kpis": _kpis(db, Subscription, SupportTicket, Affiliation, User),
        "charts": {
            "subscriptions_by_status": _group_counts(db, func, Subscription.status),
            "subscriptions_by_category": _group_counts(db, func, Subscription.type),
            "tickets_by_status": _group_counts(db, func, SupportTicket.status),
            "signups_per_month": _signups_per_month(db, User),
        },
        "tables": {
            "expiring_subscriptions": _expiring_subscriptions(db, func, Subscription),
            "open_tickets": _latest_open_tickets(db, SupportTicket),
            "latest_signups": _latest_signups(db, User),
            "pending_affiliations": _pending_affiliations(db, Affiliation),
        },
    }


class AdminDashboardIndexView(IndexView):
    @expose("/")
    def index(self):
        if not _is_admin():
            return super().index()
        return self.render_template("dashboard/index.html", **build_dashboard_context())
