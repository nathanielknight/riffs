from django.contrib import admin

from .models import Interval, PushSubscription


@admin.register(Interval)
class IntervalAdmin(admin.ModelAdmin):
    list_display = ["project", "note", "start", "end"]
    list_filter = ["start", "project"]
    search_fields = ["project", "note"]
    date_hierarchy = "start"


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user_agent", "created_at"]
