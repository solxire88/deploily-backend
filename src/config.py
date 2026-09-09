import json
import os
import urllib.request
from datetime import timedelta

from flask_appbuilder.security.manager import AUTH_OAUTH

basedir = os.path.abspath(os.path.dirname(__file__))

KEYKCLOAK_URL = os.getenv("KEYKCLOAK_URL", "")
KEYKCLOAK_REALM_NAME = os.getenv("KEYCLOAK_REALM_NAME", "myrealm")
KEYKCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET")

KEYKCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "deploily")
KEYKCLOAK_LOGOUT_REDIRECT_URL = (
    f"{KEYKCLOAK_URL}/realms/{KEYKCLOAK_REALM_NAME}/protocol/openid-connect/logout"
)


# REALM_NAME = os.getenv("REALM_NAME", "myrealm")
# CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# CLIENT_ID = os.getenv("CLIENT_ID", "deploily")
# LOGOUT_REDIRECT_URL = f"{KEYKCLOAK_URL}/realms/{REALM_NAME}/protocol/openid-connect/logout"

OAUTH_PROVIDERS = [
    {
        "name": "keycloak",
        "token_key": "access_token",
        "icon": "fa-address-card",
        "remote_app": {
            "jwks_uri": f"{KEYKCLOAK_URL}/realms/{KEYKCLOAK_REALM_NAME}/protocol/openid-connect/certs",
            "client_id": KEYKCLOAK_CLIENT_ID,
            "client_secret": KEYKCLOAK_CLIENT_SECRET,
            "api_base_url": f"{KEYKCLOAK_URL}/realms/{KEYKCLOAK_REALM_NAME}/protocol/openid-connect",
            "access_token_url": f"{KEYKCLOAK_URL}/realms/{KEYKCLOAK_REALM_NAME}/protocol/openid-connect/token",
            "authorize_url": f"{KEYKCLOAK_URL}/realms/{KEYKCLOAK_REALM_NAME}/protocol/openid-connect/auth",
            "client_kwargs": {"scope": "openid email profile roles"},
        },
    }
]

public_key_url = f"{KEYKCLOAK_URL}/realms/{KEYKCLOAK_REALM_NAME}"

JWT_ALGORITHM = "RS256"


# def fetch_keycloak_rs256_public_cert():
#     with urllib.request.urlopen(public_key_url) as response:  # noqa: S310
#         public_key_url_response = json.load(response)
#     public_key = public_key_url_response["public_key"]
#     if public_key:
#         pem_lines = [
#             "-----BEGIN PUBLIC KEY-----",
#             public_key,
#             "-----END PUBLIC KEY-----",
#         ]
#         cert_pem = "\n".join(pem_lines)
#     else:
#         cert_pem = "No cert found"
#     return cert_pem


def fetch_keycloak_rs256_public_cert():
    try:
        with urllib.request.urlopen(public_key_url) as response:  # noqa: S310
            public_key_url_response = json.load(response)
            public_key = public_key_url_response["public_key"]
            if public_key:
                pem_lines = [
                    "-----BEGIN PUBLIC KEY-----",
                    public_key,
                    "-----END PUBLIC KEY-----",
                ]
                cert_pem = "\n".join(pem_lines)
            else:
                cert_pem = "No cert found"
            return cert_pem
    except urllib.error.URLError as e:
        print(f"WARNING: Could not connect to Keycloak at {public_key_url}: {e}")
        return None
    except (KeyError, json.JSONDecodeError) as e:
        print(f"WARNING: Unexpected Keycloak response: {e}")
        return None


JWT_PUBLIC_KEY = fetch_keycloak_rs256_public_cert()
FAB_ADD_SECURITY_API = False

# Your App secret key
SECRET_KEY = os.getenv("SECRET_KEY", "abcdefghijklmnopqrtu")


JWT_PUBLIC_KEY = fetch_keycloak_rs256_public_cert()
JWT_ALGORITHM = "RS256"
AUTH_TYPE = AUTH_OAUTH
LOGOUT_REDIRECT_URL = (
    f"{KEYKCLOAK_URL}/realms/{KEYKCLOAK_REALM_NAME}/protocol/openid-connect/logout"
)


RECAPTCHA_PUBLIC_KEY = ""
RECAPTCHA_PRIVATE_KEY = ""

# The SQLAlchemy connection string.
SQLLITE_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "app.db")
SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", SQLLITE_DATABASE_URI)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Flask-WTF flag for CSRF
CSRF_ENABLED = False
FAB_API_SWAGGER_UI = True
FAB_OPENAPI_SERVERS = [
    {"url": "http://localhost:5000/"},
    {"url": "http://localhost:5001/"},
    {"url": "http://192.168.1.22:5000"},
    {"url": "http://192.168.1.21:5000"},
    {"url": "http://192.168.1.15:5000"},
    {"url": "http://192.168.1.16:5000"},
]
BACKEND_ADMIN_URL = os.getenv("BACKEND_ADMIN_URL", False)
PDF_RECEIPT_URL = os.getenv("PDF_RECEIPT_URL", "")
SEND_RECEIPT_MAIL_URL = os.getenv("SEND_RECEIPT_MAIL_URL", "")

if BACKEND_ADMIN_URL:
    FAB_OPENAPI_SERVERS.append({"url": BACKEND_ADMIN_URL})


DEFAULT_CREDIT_AMOUNT = float(os.getenv("DEFAULT_CREDIT_AMOUNT", "10000"))


# config.py — add these at the bottom

KEYCLOAK_TOKEN_URL = f"{KEYKCLOAK_URL}/realms/{KEYKCLOAK_REALM_NAME}/protocol/openid-connect/token"
KEYCLOAK_AUTH_URL = f"{KEYKCLOAK_URL}/realms/{KEYKCLOAK_REALM_NAME}/protocol/openid-connect/auth"


# OAuth2 config for Swagger UI "Authorize" button
SWAGGER_UI_OAUTH2_CONFIG = {
    "clientId": KEYKCLOAK_CLIENT_ID,
    "clientSecret": KEYKCLOAK_CLIENT_SECRET,
    "appName": "Deploily API",
    "scopeSeparator": " ",
    "scopes": "openid email profile roles",
}

# OpenAPI security scheme injected into the spec
FAB_OPENAPI_SECURITY_DEFINITIONS = {
    "oauth2_keycloak": {
        "type": "oauth2",
        "flows": {
            "password": {
                "tokenUrl": KEYCLOAK_TOKEN_URL,
                "scopes": {
                    "openid": "OpenID Connect",
                    "profile": "User profile",
                    "email": "User email",
                    "roles": "User roles",
                },
            },
        },
    }
}

FAB_API_SWAGGER_TEMPLATE = "swagger/swagger.html"
# Pre-fill client credentials so user doesn't have to type them
FAB_SWAGGER_UI_OAUTH2_CONFIG = {
    "clientId": KEYKCLOAK_CLIENT_ID,
    "clientSecret": KEYKCLOAK_CLIENT_SECRET,
    "usePkceWithAuthorizationCodeGrant": False,
}

# ------------------------------
# GLOBALS FOR APP Builder
# ------------------------------
# Uncomment to setup Your App name
# APP_NAME = "My App Name"

# Uncomment to setup Setup an App icon
# APP_ICON = "static/img/logo.jpg"

JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
# ----------------------------------------------------
# AUTHENTICATION CONFIG
# ----------------------------------------------------
# The authentication type
# AUTH_OID : Is for OpenID
# AUTH_DB : Is for database (username/password()
# AUTH_LDAP : Is for LDAP
# AUTH_REMOTE_USER : Is for using REMOTE_USER from web server
AUTH_TYPE = AUTH_OAUTH

# Uncomment to setup Full admin role name
# AUTH_ROLE_ADMIN = 'Admin'

# Uncomment to setup Public role name, no authentication needed
AUTH_ROLE_PUBLIC = "Public"

# Will allow user self registration
AUTH_USER_REGISTRATION = True

# The default user self registration role
# AUTH_USER_REGISTRATION_ROLE = "Public"

# The default user self registration role
AUTH_USER_REGISTRATION_ROLE = "User"

FAB_ROLES = {
    "User": [
        ["MyFavoritesModelApi", "can_add_remove_favorite"],
        ["ConsumerApi", "can_post"],
        ["ContactUSModelApi", "can_get"],
        ["ContactUSModelApi", "can_info"],
        # ["ContactUSModelApi", "can_put"],
        ["ContactUSModelApi", "can_post"],
        # ["ContactUSModelApi", "can_delete"],
        ["CommentModelApi", "can_get"],
        ["CommentModelApi", "can_post"],
        ["CommentModelApi", "can_info"],
        ["CommentModelApi", "can_put"],
        ["CommentModelApi", "can_delete"],
        ["MyFavoritesApi", "can_post"],
        ["MyFavoritesModelApi", "can_get"],
        ["MyFavoritesModelApi", "can_put"],
        ["MyFavoritesModelApi", "can_post"],
        ["MyFavoritesModelApi", "can_delete"],
        ["PaymentModelApi", "can_get"],
        # ["PaymentModelApi", "can_put"],
        ["PaymentModelApi", "can_post"],
        ["PaymentModelApi", "can_upload_receipt"],
        # ["PaymentModelApi", "can_delete"],
        ["StatusApi", "can_get"],
        ["RatingApi", "can_create_or_update_rating"],
        ["PaymentProfileModelApi", "can_get"],
        ["PaymentProfileModelApi", "can_put"],
        ["PaymentProfileModelApi", "can_post"],
        ["PaymentProfileModelApi", "can_delete"],
        ["PromoCodeApi", "can_post"],
        ["ServiceModelApi", "can_get"],
        # ["ServiceModelApi", "can_put"],
        # ["ServiceModelApi", "can_post"],
        # ["ServiceModelApi", "can_delete"],
        ["ApiServiceModelApi", "can_get"],
        # ["ApiServiceModelApi", "can_put"],
        # ["ApiServiceModelApi", "can_post"],
        # ["ApiServiceModelApi", "can_delete"],
        ["AppServiceModelApi", "can_get"],
        # ["AppServiceModelApi", "can_put"],
        # ["AppServiceModelApi", "can_post"],
        # ["AppServiceModelApi", "can_delete"],
        ["CicdServiceModelApi", "can_get"],
        # ["CicdServiceModelApi", "can_put"],
        # ["CicdServiceModelApi", "can_post"],
        # ["CicdServiceModelApi", "can_delete"],
        ["RessourcesServiceModelApi", "can_get"],
        # ["RessourcesServiceModelApi", "can_put"],
        # ["RessourcesServiceModelApi", "can_post"],
        # ["RessourcesServiceModelApi", "can_delete"],
        ["ProvidersRessourceServiceModelApi", "can_get"],
        # ["ProvidersRessourceServiceModelApi", "can_put"],
        # ["ProvidersRessourceServiceModelApi", "can_post"],
        # ["ProvidersRessourceServiceModelApi", "can_delete"],
        ["AffiliationModelApi", "can_get"],
        ["AffiliationModelApi", "can_put"],
        ["AffiliationModelApi", "can_post"],
        ["AffiliationModelApi", "can_delete"],
        ["AffiliationModelApi", "can_create_affiliation"],
        ["ServicePlanModelApi", "can_get"],
        # ["ServicePlanModelApi", "can_put"],
        # ["ServicePlanModelApi", "can_post"],
        # ["ServicePlanModelApi", "can_delete"],
        ["ServiceTagModelApi", "can_get"],
        # ["ServiceTagModelApi", "can_put"],
        # ["ServiceTagModelApi", "can_post"],
        # ["ServiceTagModelApi", "can_delete"],
        ["SubscriptionModelApi", "can_get"],
        ["SubscriptionModelApi", "can_put"],
        ["SubscriptionModelApi", "can_post"],
        # ["ServiceTagModelApi", "can_delete"],
        ["SubscriptionModelApi", "can_delete"],
        ["SubscriptionModelApi", "can_create_my_service_consumer"],
        ["ServiceRessouceCategoryModelApi", "can_get"],
        # ["ServiceRessouceCategoryModelApi", "can_put"],
        # ["ServiceRessouceCategoryModelApi", "can_post"],
        # ["ServiceRessouceCategoryModelApi", "can_delete"],
        ["SubscriptionApi", "can_post"],
        ["SubscriptionApi", "can_subscribe_to_plan"],
        ["AccountFundingApi", "can_fund_balance"],
        ["SupportTicketResponseModelApi", "can_get"],
        ["SupportTicketResponseModelApi", "can_put"],
        ["SupportTicketResponseModelApi", "can_post"],
        ["SupportTicketResponseModelApi", "can_delete"],
        ["SupportTicketModelApi", "can_get"],
        ["SupportTicketModelApi", "can_put"],
        ["SupportTicketModelApi", "can_post"],
        ["SupportTicketModelApi", "can_delete"],
        ["UserModelApi", "can_get"],
        ["AppRecommendationModelApi", "can_get"],
        ["AppServiceSubscriptionModelApi", "can_get"],
        ["TtkEpayAppServiceSubscriptionModelApi", "can_get"],
        ["TtkEpayAppServiceSubscriptionModelApi", "can_put"],
        ["TtkEpayAppServiceSubscriptionModelApi", "can_post"],
        ["TtkEpaySubscriptionApi", "can_post"],
        ["ApiServiceSubscriptionModelApi", "can_get"],
        ["ApiServiceSubscriptionModelApi", "can_put"],
        ["ApiServiceSubscriptionModelApi", "can_post"],
        ["ApiServiceSubscriptionModelApi", "can_delete"],
        ["ApiServiceSubscriptionModelApi", "can_create_my_service_consumer"],
        ["TtkEpaySubscriptionApi", "can_subscribe_to_plan"],
        ["PromoCodeApi", "can_check_promo_code"],
        ["TtkEpaySubscriptionApi", "can_upgrade_app_subscription"],
        ["SubscriptionApi", "can_upgrade_api_subscription"],
        ["SubscriptionApi", "can_renew_api_subscription"],
        ["OdooAppServiceSubscriptionModelApi", "can_get"],
        ["SupabaseAppServiceSubscriptionModelApi", "can_get"],
        ["OdooSubscriptionApi", "can_subscribe_to_plan"],
        ["OdooSubscriptionApi", "can_upgrade_app_subscription"],
        ["SupabaseSubscriptionApi", "can_subscribe_to_plan"],
        ["SupabaseSubscriptionApi", "can_upgrade_app_subscription"],
        ["TtkEpaySubscription", "can_renew_app_subscription"],
        ["OdooSubscription", "can_renew_app_subscription"],
        ["SupabaseSubscription", "can_renew_app_subscription"],
        ["StatusApi", "can_send_pdf_receipt_mail"],
        ["SubscriptionModelApi", "can_history"],
        ["NextCloudSubscriptionApi", "can_subscribe_to_plan"],
        ["NextCloudSubscriptionApi", "can_upgrade_app_subscription"],
        ["NextCloudSubscriptionApi", "can_renew_app_subscription"],
        ["ManagedRessourceModelApi", "can_get"],
        ["HiEventsSubscriptionApi", "can_subscribe_to_plan"],
        ["HiEventsSubscriptionApi", "can_upgrade_app_subscription"],
        ["HiEventsSubscriptionApi", "can_renew_app_subscription"],
        ["NextCloudAppServiceSubscriptionModelApi", "can_get"],
        ["HiEventsAppServiceSubscriptionModelApi", "can_get"],
        ["DeploymentServiceModelApi", "can_get"],
        # ["DeploymentServiceModelApi", "can_post"],
        # ["DeploymentServiceModelApi", "can_put"],
        ["CustomParameterModelApi", "can_get"],
        ["CustomParameterModelApi", "can_post"],
        ["CustomParameterModelApi", "can_put"],
        ["DeploymentServiceSubscriptionModelApi", "can_get"],
        ["DeploymentServiceSubscriptionModelApi", "can_post"],
        ["DeploymentServiceSubscriptionModelApi", "can_put"],
        ["WebApplicationDeploymentServiceSubscriptionModelApi", "can_put"],
        ["WebApplicationDeploymentServiceSubscriptionModelApi", "can_get"],
        ["WebApplicationDeploymentServiceSubscriptionModelApi", "can_post"],
        ["WebApplicationDeploymentSubscriptionApi", "can_subscribe_to_plan"],
        ["MobileApplicationDeploymentServiceSubscriptionModelApi", "can_put"],
        ["MobileApplicationDeploymentServiceSubscriptionModelApi", "can_get"],
        ["MobileApplicationDeploymentServiceSubscriptionModelApi", "can_post"],
        ["MobileApplicationDeploymentSubscriptionApi", "can_subscribe_to_plan"],
        ["DashboardApi", "can_dashboard"],
        ["SupportTicketModelApi", "can_upload_image"],
    ]
}

IMG_UPLOAD_URL = "/static/uploads/"
IMG_UPLOAD_FOLDER = basedir + "/app/static/uploads/"
UPLOAD_FOLDER = basedir + "/app/static/uploads/"


# When using LDAP Auth, setup the ldap server
# AUTH_LDAP_SERVER = "ldap://ldapserver.new"

# Uncomment to setup OpenID providers example for OpenID authentication
# OPENID_PROVIDERS = [
#    { 'name': 'Yahoo', 'url': 'https://me.yahoo.com' },
#    { 'name': 'AOL', 'url': 'http://openid.aol.com/<username>' },
#    { 'name': 'Flickr', 'url': 'http://www.flickr.com/<username>' },
#    { 'name': 'MyOpenID', 'url': 'https://www.myopenid.com' }]
# ---------------------------------------------------
# Babel config for translations
# ---------------------------------------------------
# Setup default language
BABEL_DEFAULT_LOCALE = "en"
# Your application default translation path
BABEL_DEFAULT_FOLDER = "translations"
# The allowed translation for you app
LANGUAGES = {
    "en": {"flag": "gb", "name": "English"},
    "fr": {"flag": "fr", "name": "French"},
    "pt": {"flag": "pt", "name": "Portuguese"},
    "pt_BR": {"flag": "br", "name": "Pt Brazil"},
    "es": {"flag": "es", "name": "Spanish"},
    "de": {"flag": "de", "name": "German"},
    "zh": {"flag": "cn", "name": "Chinese"},
    "ru": {"flag": "ru", "name": "Russian"},
}

APISIX_ADMIN_URL = os.getenv("APISIX_ADMIN_URL", "http://admin-api.deploily.cloud/apisix/admin")
APISIX_API_KEY = os.getenv("APISIX_API_KEY", "edd1c9f034335f136f87ad84b625c8f1")
MAIL_HOST = os.getenv("MAIL_HOST")
MAIL_PORT = int(os.getenv("MAIL_PORT", 465))
MAIL_USERNAME = os.getenv("MAIL_USER")
MAIL_PASSWORD = os.getenv("MAIL_PASS")
MAIL_USE_SSL = True

SCHEDULER_EXECUTORS = {"default": {"type": "threadpool", "max_workers": 1}}
SCHEDULER_JOB_DEFAULTS = {"coalesce": False, "max_instances": 1}

SCHEDULER_ENABLED = os.getenv("SCHEDULER_ENABLED", "True")

NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL")
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL")

# Per-identity SMTP credentials, only needed once a real separate account
# exists for that identity (falls back to the single MAIL_USER/MAIL_PASS
# account below until then). Host/port are per-identity too since each
# account can live on a different mail provider -- they default to the
# global MAIL_HOST/MAIL_PORT only when unset.
MAIL_CONNECT_ADDRESS = os.getenv("MAIL_CONNECT_ADDRESS")
MAIL_CONNECT_USER = os.getenv("MAIL_CONNECT_USER")
MAIL_CONNECT_PASS = os.getenv("MAIL_CONNECT_PASS")
MAIL_CONNECT_HOST = os.getenv("MAIL_CONNECT_HOST") or MAIL_HOST
MAIL_CONNECT_PORT = int(os.getenv("MAIL_CONNECT_PORT") or MAIL_PORT)

MAIL_SUPPORT_ADDRESS = os.getenv("MAIL_SUPPORT_ADDRESS")
MAIL_SUPPORT_USER = os.getenv("MAIL_SUPPORT_USER")
MAIL_SUPPORT_PASS = os.getenv("MAIL_SUPPORT_PASS")
MAIL_SUPPORT_HOST = os.getenv("MAIL_SUPPORT_HOST") or MAIL_HOST
MAIL_SUPPORT_PORT = int(os.getenv("MAIL_SUPPORT_PORT") or MAIL_PORT)

# Sender address -> SMTP login credentials + server. Looked up at send time
# from Mail.email_from -- no separate "which account" flag anywhere. Every
# address that currently sends mail (MAIL_USERNAME, NOTIFICATION_EMAIL,
# SUPPORT_EMAIL) defaults to the one configured account, so this is a
# no-op until MAIL_CONNECT_*/MAIL_SUPPORT_* are actually set to distinct
# accounts.
MAIL_ACCOUNTS = {}
if MAIL_USERNAME and MAIL_PASSWORD:
    for _addr in filter(None, {MAIL_USERNAME, NOTIFICATION_EMAIL, SUPPORT_EMAIL}):
        MAIL_ACCOUNTS[_addr] = {
            "user": MAIL_USERNAME,
            "pass": MAIL_PASSWORD,
            "host": MAIL_HOST,
            "port": MAIL_PORT,
        }

for _addr, _user, _pass, _host, _port in (
    (MAIL_CONNECT_ADDRESS, MAIL_CONNECT_USER, MAIL_CONNECT_PASS, MAIL_CONNECT_HOST, MAIL_CONNECT_PORT),
    (MAIL_SUPPORT_ADDRESS, MAIL_SUPPORT_USER, MAIL_SUPPORT_PASS, MAIL_SUPPORT_HOST, MAIL_SUPPORT_PORT),
):
    if _addr and _user and _pass and _host:
        MAIL_ACCOUNTS[_addr] = {"user": _user, "pass": _pass, "host": _host, "port": _port}


CAPTCHA_SECRET_KEY = os.getenv("CAPTCHA_SECRET_KEY")

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "False")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "False")

CACHE_TYPE = os.getenv("CACHE_TYPE", "NullCache")
CACHE_REDIS_HOST = os.getenv("CACHE_REDIS_HOST", "redis")
CACHE_REDIS_PORT = os.getenv("CACHE_REDIS_PORT", "6379")
CACHE_REDIS_DB = os.getenv("CACHE_REDIS_DB", "0")
CACHE_REDIS_URL = os.getenv("CACHE_REDIS_URL", "redis://redis:6379/0")
CACHE_DEFAULT_TIMEOUT = os.getenv("CACHE_DEFAULT_TIMEOUT", "500")
DURATION_MONTHS = int(os.getenv("DURATION_MONTHS", 3))
