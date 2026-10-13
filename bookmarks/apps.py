from riffs import riffs_app


class BookmarksConfig(riffs_app.RiffsAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bookmarks"
    has_views = True
    is_public = True
