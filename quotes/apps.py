from riffs.riffs_app import RiffsAppConfig


class QuotesConfig(RiffsAppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'quotes'
    has_views = False
    is_public = False
