from riffs import riffs_app


class DropfeedConfig(riffs_app.RiffsAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dropfeed"
    verbose_name = "DropFeed Podcast Manager"
    has_views = True
    is_public = False

    def ready(self):
        import dropfeed.models
