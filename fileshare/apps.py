from riffs.riffs_app import RiffsAppConfig


class FileshareConfig(RiffsAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "fileshare"
    has_views = True
    is_public = False
