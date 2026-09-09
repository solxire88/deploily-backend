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


def _month_bounds():
    now = datetime.now()
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
    return this_month_start, last_month_start


def _kpi_with_trend(db, Model, total_filter, positive_is_good):
    # "Trend vs last month" compares how many matching rows were *created*
    # this calendar month vs last calendar month -- there's no history/
    # snapshot table to reconstruct past point-in-time status counts, so
    # this approximates the trend via creation-date volume instead.
    this_month_start, last_month_start = _month_bounds()

    total = db.session.query(Model).filter(total_filter).count()
    this_month = (
        db.session.query(Model)
        .filter(total_filter, Model.created_on >= this_month_start)
        .count()
    )
    last_month = (
        db.session.query(Model)
        .filter(
            total_filter,
            Model.created_on >= last_month_start,
            Model.created_on < this_month_start,
        )
        .count()
    )
    return {
        "value": total,
        "delta": this_month - last_month,
        "positive_is_good": positive_is_good,
        "sparkline": list(_monthly_counts(db, Model, total_filter).values()),
    }


def _kpis(db, Subscription, SupportTicket, Affiliation, User):
    from sqlalchemy import true

    return {
        "active_subscriptions": _kpi_with_trend(
            db, Subscription, Subscription.status == "active", positive_is_good=True
        ),
        "open_tickets": _kpi_with_trend(
            db, SupportTicket, SupportTicket.status == "open", positive_is_good=False
        ),
        "pending_affiliations": _kpi_with_trend(
            db, Affiliation, Affiliation.affiliation_state == "pending", positive_is_good=False
        ),
        "total_users": _kpi_with_trend(db, User, true(), positive_is_good=True),
    }


def _group_counts(db, func, column):
    rows = db.session.query(column, func.count()).group_by(column).all()
    return {str(label) if label is not None else "unknown": count for label, count in rows}


def _monthly_counts(db, Model, extra_filter=None):
    since = datetime.now() - timedelta(days=30 * _MONTHS_BACK)
    query = db.session.query(Model.created_on).filter(
        Model.created_on.isnot(None), Model.created_on >= since
    )
    if extra_filter is not None:
        query = query.filter(extra_filter)
    rows = query.all()

    buckets = OrderedDict()
    cursor = since.replace(day=1)
    for _ in range(_MONTHS_BACK + 1):
        buckets[cursor.strftime("%Y-%m")] = 0
        cursor = (cursor + timedelta(days=32)).replace(day=1)

    for (created_on,) in rows:
        key = created_on.strftime("%Y-%m")
        if key in buckets:
            buckets[key] += 1

    return buckets


_SUBSCRIPTION_CATEGORY_LABELS = {
    "subscription": "General",
    "subscription_app_service": "App Service",
    "subscription_api_service": "API Service",
    "subscription_deployment_service": "Deployment Service",
    "subscription_ressource_service": "Resource Service",
}


def _pretty_category(raw):
    if not raw:
        return "Unknown"
    return _SUBSCRIPTION_CATEGORY_LABELS.get(raw, raw.replace("_", " ").title())


def _subscriptions_by_category_status(db, func, Subscription):
    # One combined view instead of two separate pies -- shows whether
    # errors/inactive subscriptions cluster in a particular category.
    rows = (
        db.session.query(Subscription.type, Subscription.status, func.count())
        .group_by(Subscription.type, Subscription.status)
        .all()
    )
    unordered = OrderedDict()
    for category, status, count in rows:
        label = _pretty_category(category)
        status = status or "unknown"
        unordered.setdefault(label, {})[status] = count

    # General first, then the rest in the same fixed order as the label map
    # above -- not left to whatever order the DB's GROUP BY happens to return.
    ordered_labels = list(_SUBSCRIPTION_CATEGORY_LABELS.values())
    data = OrderedDict()
    for label in ordered_labels:
        if label in unordered:
            data[label] = unordered.pop(label)
    data.update(unordered)  # anything unmapped (e.g. "Unknown") goes last
    return data


def _ticket_age_histogram(db, SupportTicket):
    # How long open tickets have been sitting, not just how many are open --
    # more actionable than a static open/closed split.
    now = datetime.now()
    rows = (
        db.session.query(SupportTicket.created_on)
        .filter(SupportTicket.status == "open", SupportTicket.created_on.isnot(None))
        .all()
    )
    buckets = OrderedDict([("0-2 days", 0), ("3-5 days", 0), ("6-7 days", 0), ("8+ days", 0)])
    for (created_on,) in rows:
        days = (now - created_on).days
        if days <= 2:
            buckets["0-2 days"] += 1
        elif days <= 5:
            buckets["3-5 days"] += 1
        elif days <= 7:
            buckets["6-7 days"] += 1
        else:
            buckets["8+ days"] += 1
    return buckets


def _expiring_subscriptions(db, func, Subscription, days=7):
    now = datetime.now()
    horizon = now + timedelta(days=days)
    expiry_date = func.make_interval(0, Subscription.duration_month) + Subscription.start_date

    subs = (
        db.session.query(Subscription)
        .filter(Subscription.status == "active", expiry_date >= now, expiry_date <= horizon)
        .order_by(expiry_date.asc())
        .limit(20)
        .all()
    )
    return [
        (s, max(0, (s.start_date + timedelta(days=30 * s.duration_month) - now).days))
        for s in subs
    ]


def _churn_per_month(db, Subscription):
    # Same "changed_on as proxy for went-inactive-on" caveat as _recently_churned.
    since = datetime.now() - timedelta(days=30 * _MONTHS_BACK)
    rows = (
        db.session.query(Subscription.changed_on)
        .filter(Subscription.status == "inactive", Subscription.changed_on >= since)
        .all()
    )
    buckets = OrderedDict()
    cursor = since.replace(day=1)
    for _ in range(_MONTHS_BACK + 1):
        buckets[cursor.strftime("%Y-%m")] = 0
        cursor = (cursor + timedelta(days=32)).replace(day=1)
    for (changed_on,) in rows:
        if not changed_on:
            continue
        key = changed_on.strftime("%Y-%m")
        if key in buckets:
            buckets[key] += 1
    return buckets


def _recently_churned(db, Subscription, days=30):
    # No dedicated "went inactive on" timestamp exists -- changed_on (AuditMixin)
    # is the closest available proxy, same caveat as the KPI trend deltas above.
    since = datetime.now() - timedelta(days=days)
    return (
        db.session.query(Subscription)
        .filter(Subscription.status == "inactive", Subscription.changed_on >= since)
        .order_by(Subscription.changed_on.desc())
        .limit(20)
        .all()
    )


def _latest_open_tickets(db, SupportTicket):
    now = datetime.now()
    tickets = (
        db.session.query(SupportTicket)
        .filter(SupportTicket.status == "open")
        .order_by(SupportTicket.created_on.desc())
        .limit(20)
        .all()
    )
    return [(t, (now - t.created_on).days if t.created_on else 0) for t in tickets]


def _unverified_accounts(db, User):
    return (
        db.session.query(User)
        .filter(User.active.is_(False))
        .order_by(User.created_on.desc())
        .limit(20)
        .all()
    )


def _pending_affiliations(db, Affiliation):
    now = datetime.now()
    rows = (
        db.session.query(Affiliation)
        .filter(Affiliation.affiliation_state == "pending")
        .order_by(Affiliation.created_on.desc())
        .limit(20)
        .all()
    )
    return [
        (a, (now - a.created_on).days if a.created_on else 0) for a in rows
    ]


def _new_leads(db, ContactUs):
    return (
        db.session.query(ContactUs)
        .filter(ContactUs.contact_us_status == "new")
        .order_by(ContactUs.created_on.desc())
        .limit(20)
        .all()
    )


def _failed_emails(db, Mail):
    return (
        db.session.query(Mail)
        .filter(Mail.mail_state == "error")
        .order_by(Mail.created_on.desc())
        .limit(20)
        .all()
    )


def _stuck_emails(db, Mail, hours=1):
    # "outGoing" and older than `hours` -- the send task never ran or hung,
    # a genuinely different failure mode than an explicit "error" state.
    cutoff = datetime.now() - timedelta(hours=hours)
    return (
        db.session.query(Mail)
        .filter(Mail.mail_state == "outGoing", Mail.created_on < cutoff)
        .order_by(Mail.created_on.asc())
        .limit(20)
        .all()
    )


def _errored_deployments(db, SubscriptionAppService, SubscriptionDeploymentService):
    app_errors = (
        db.session.query(SubscriptionAppService)
        .filter(SubscriptionAppService.application_status == "error")
        .all()
    )
    deployment_errors = (
        db.session.query(SubscriptionDeploymentService)
        .filter(SubscriptionDeploymentService.deployment_status == "error")
        .all()
    )
    combined = [("App", s) for s in app_errors] + [
        ("Deployment", s) for s in deployment_errors
    ]
    combined.sort(key=lambda pair: pair[1].created_on or datetime.min, reverse=True)
    return combined[:20]


def _stuck_deployments(db, SubscriptionAppService, SubscriptionDeploymentService, hours=24):
    # "processing" for longer than `hours` -- the deployment pipeline never
    # finished, distinct from an explicit "error" state and easy to miss
    # since nothing else flags it.
    cutoff = datetime.now() - timedelta(hours=hours)
    app_stuck = (
        db.session.query(SubscriptionAppService)
        .filter(
            SubscriptionAppService.application_status == "processing",
            SubscriptionAppService.created_on < cutoff,
        )
        .all()
    )
    deployment_stuck = (
        db.session.query(SubscriptionDeploymentService)
        .filter(
            SubscriptionDeploymentService.deployment_status == "processing",
            SubscriptionDeploymentService.created_on < cutoff,
        )
        .all()
    )
    combined = [("App", s) for s in app_stuck] + [("Deployment", s) for s in deployment_stuck]
    combined.sort(key=lambda pair: pair[1].created_on or datetime.min)
    now = datetime.now()
    return [
        (kind, s, (now - s.created_on).days if s.created_on else 0)
        for kind, s in combined[:20]
    ]


def _never_responded_tickets(db, SupportTicket):
    from app.schedulers.support_ticket_tasks import _last_sent_response

    now = datetime.now()
    open_tickets = (
        db.session.query(SupportTicket)
        .filter(SupportTicket.status == "open")
        .order_by(SupportTicket.created_on.desc())
        .all()
    )
    never = [t for t in open_tickets if _last_sent_response(t) is None][:20]
    return [(t, (now - t.created_on).days if t.created_on else 0) for t in never]


def _first_response_hours(ticket):
    sent = [r for r in ticket.support_ticket_responses if r.status == "sent"]
    if not sent or not ticket.created_on:
        return None
    first = min(sent, key=lambda r: r.changed_on)
    if not first.changed_on:
        return None
    hours = (first.changed_on - ticket.created_on).total_seconds() / 3600.0
    return hours if hours >= 0 else None


def _avg_first_response_hours(db, SupportTicket):
    tickets = db.session.query(SupportTicket).all()
    hours = [h for h in (_first_response_hours(t) for t in tickets) if h is not None]
    if not hours:
        return None
    return round(sum(hours) / len(hours), 1)


def build_dashboard_context():
    # Imported lazily: this module is imported before models/db finish wiring
    # up during app init (AdminDashboardIndexView must exist before
    # AppBuilder() is constructed), so these can't be top-level imports.
    from sqlalchemy import func

    from app import db
    from app.core.models.subscription_models import Subscription
    from app.core.models.support_ticket_models import SupportTicket
    from app.core.models.contact_us_models import ContactUs
    from app.core.models.mail_models import Mail
    from app.core.models.payment_models import Payment
    from app.service_ressources.models.affiliation_model import Affiliation
    from app.service_apps.models.app_service_subscription_model import SubscriptionAppService
    from app.service_deployment.models.deployment_service_subscription_model import (
        SubscriptionDeploymentService,
    )
    from flask_appbuilder.security.sqla.models import User

    return {
        "kpis": _kpis(db, Subscription, SupportTicket, Affiliation, User),
        "avg_first_response_hours": _avg_first_response_hours(db, SupportTicket),
        "charts": {
            "subscriptions_by_category_status": _subscriptions_by_category_status(
                db, func, Subscription
            ),
            "ticket_age_histogram": _ticket_age_histogram(db, SupportTicket),
            "signups_per_month": _monthly_counts(db, User),
            "payment_status": _group_counts(db, func, Payment.status),
            "churn_per_month": _churn_per_month(db, Subscription),
        },
        "tables": {
            "expiring_7": _expiring_subscriptions(db, func, Subscription, days=7),
            "expiring_15": _expiring_subscriptions(db, func, Subscription, days=15),
            "expiring_30": _expiring_subscriptions(db, func, Subscription, days=30),
            "recently_churned": _recently_churned(db, Subscription),
            "open_tickets": _latest_open_tickets(db, SupportTicket),
            "unverified_accounts": _unverified_accounts(db, User),
            "pending_affiliations": _pending_affiliations(db, Affiliation),
            "new_leads": _new_leads(db, ContactUs),
            "never_responded": _never_responded_tickets(db, SupportTicket),
            "failed_emails": _failed_emails(db, Mail),
            "stuck_emails": _stuck_emails(db, Mail),
            "errored_deployments": _errored_deployments(
                db, SubscriptionAppService, SubscriptionDeploymentService
            ),
            "stuck_deployments": _stuck_deployments(
                db, SubscriptionAppService, SubscriptionDeploymentService
            ),
        },
    }


class AdminDashboardIndexView(IndexView):
    @expose("/")
    def index(self):
        if not _is_admin():
            return super().index()
        return self.render_template("dashboard/index.html", **build_dashboard_context())
