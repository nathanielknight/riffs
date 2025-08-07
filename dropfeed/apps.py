from django.apps import AppConfig


class DropfeedConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dropfeed'
    verbose_name = 'DropFeed Podcast Manager'
    
    def ready(self):
        import dropfeed.models
