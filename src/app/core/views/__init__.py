from app import appbuilder, db

# Master
from . import service_views
from . import service_tag_views
from . import plan_views
from . import service_plan_views
from . import service_plan_option_views
from . import media_views
from . import service_parameter_view

# Operations
from . import contact_us
from . import support_ticket_views
from . import support_ticket_response_views
from . import my_favorites_views
from . import mail_views
from . import email_template_views
from . import comment_views
from . import advertisment_views
from . import rating_views

# Subscriptions
from . import managed_ressource_view
from . import subscription_views

# Billing
from . import payment_views
from . import payment_profile_views
from . import promo_code_views
