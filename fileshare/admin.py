from django.contrib import admin
from .models import ShareFile


@admin.register(ShareFile)
class ShareFileAdmin(admin.ModelAdmin):
    list_display = ["title", "share_key", "expiration", "created_at", "is_expired"]
    readonly_fields = ["share_key", "created_at", "updated_at"]
    list_filter = ["expiration", "created_at"]
    search_fields = ["title", "share_key"]

    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = "Expired"
