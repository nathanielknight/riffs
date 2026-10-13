from riffs import riffs_app


class QuotesConfig(riffs_app.RiffsAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "quotes"
    has_views = False
    is_public = False
