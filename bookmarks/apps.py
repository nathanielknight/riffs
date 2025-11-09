from riffs.riffs_app import RiffsAppConfig


class BookmarksConfig(RiffsAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bookmarks"
    has_views = True
    is_public = True
