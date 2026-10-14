from riffs import riffs_app


class TimetrackConfig(riffs_app.RiffsAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "timetrack"
    verbose_name = "Time Tracker"
    has_views = True
    is_public = False
