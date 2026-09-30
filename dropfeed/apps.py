from riffs.riffs_app import RiffsAppConfig


class DropfeedConfig(RiffsAppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dropfeed'
    verbose_name = 'DropFeed Podcast Manager'
    has_views = True
    is_public = False

    def ready(self):
        import dropfeed.models
