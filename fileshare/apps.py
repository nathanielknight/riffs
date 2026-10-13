from riffs import riffs_app


class FileshareConfig(riffs_app.RiffsAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "fileshare"
    has_views = False
    is_public = False
