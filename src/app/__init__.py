import logging
from celery import Celery
from flask import Flask
from flask_appbuilder import SQLA, AppBuilder
from flask_cors import CORS
from flask_migrate import Migrate
from sqlalchemy import MetaData
from app.custom_sso_security_manager import CustomSsoSecurityManager
import os
from app.custom_sso_security_manager import SecurityApi  # ← new

template_folder = os.path.join(os.path.dirname(__file__), "templates")
app = Flask(__name__, template_folder=template_folder)
# app = Flask(__name__)
app.config.from_object("config")

# TODO move urls to .env | localhost should only be available for dev
CORS(
    app,
    resources={
        r"/api/*": {"origins": "[“http://localhost:3000”, “https://console.deploily.cloud“]"}
    },
    origins=["http://localhost:3000", "https://console.deploily.cloud"],
)


convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)
db = SQLA(app, metadata=metadata)

migrate = Migrate(app, db, render_as_batch=True)

# appbuilder = AppBuilder(app, db.session)
appbuilder = AppBuilder(app, db.session, security_manager_class=CustomSsoSecurityManager)


"""Cron configuartion"""
if app.config["SCHEDULER_ENABLED"] in ["True", "true", "t", "1"]:
    from flask_apscheduler import APScheduler

    scheduler = APScheduler()
    scheduler.init_app(app)
    logging.getLogger("apscheduler").setLevel(logging.INFO)
    from . import schedulers

    scheduler.start()
# Register views


# Configure Celery
app.config["CELERY_BROKER_URL"] = app.config["CACHE_REDIS_URL"]
app.config["CELERY_RESULT_BACKEND"] = app.config["CACHE_REDIS_URL"]

# Initialize Celery
celery = Celery(
    app.name,
    broker=app.config["CACHE_REDIS_URL"],
    backend=app.config["CELERY_RESULT_BACKEND"],
)
celery.conf.update(app.config)
# ---------------------------------------------------
# Register CLI commands  ✅ VERY IMPORTANT
# ---------------------------------------------------

from cli.seed import seed

app.cli.add_command(seed)

if __name__ == "__main__":
    app.run(debug=True)

from .service_ressources import models
from .core import models, views, controllers
from .service_api import models, views, controllers
from .service_apps import models, views, controllers
from .service_deployment import models, views, controllers
from .promo_code import models, views, controllers
from . import services, schedulers
from .service_ressources import views, controllers


appbuilder.add_link(
    name="Swagger documentation",
    href="/swagger/v1",
    icon="fa-solid fa-book",
    category="Configuration",
)
