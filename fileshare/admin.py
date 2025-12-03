from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import ShareFile


@admin.register(ShareFile)
class ShareFileAdmin(admin.ModelAdmin):
    list_display = ["title", "share_link_display", "expiration", "created_at", "is_expired"]
    readonly_fields = ["share_key", "share_link", "created_at", "updated_at"]
    list_filter = ["expiration", "created_at"]
    search_fields = ["title", "share_key"]

    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = "Expired"

    def share_link(self, obj):
        """Display the full share link with copy functionality"""
        if obj.pk:
            url = self._get_share_url(obj)
            return format_html(
                '<input type="text" value="{}" readonly '
                'style="width: 500px; padding: 5px; font-family: monospace;" '
                'onclick="this.select(); document.execCommand(\'copy\'); '
                'alert(\'Link copied to clipboard!\');" /> '
                '<a href="{}" target="_blank" style="margin-left: 10px;">Open</a>',
                url, url
            )
        return "-"
    share_link.short_description = "Share Link (click to copy)"

    def share_link_display(self, obj):
        """Shortened display for list view"""
        if obj.pk:
            url = self._get_share_url(obj)
            return format_html(
                '<a href="{}" target="_blank" title="{}">📋 Copy Link</a>',
                url, url
            )
        return "-"
    share_link_display.short_description = "Share Link"

    def _get_share_url(self, obj):
        """Helper to construct the absolute share URL"""
        from django.contrib.sites.shortcuts import get_current_site
        from django.conf import settings

        path = reverse("fileshare:serve", kwargs={"share_key": obj.share_key})

        # Try to build a proper URL
        # In production, this should use ALLOWED_HOSTS or a configured domain
        if hasattr(settings, 'ALLOWED_HOSTS') and settings.ALLOWED_HOSTS:
            # Use the first non-localhost host if available
            hosts = [h for h in settings.ALLOWED_HOSTS if h not in ['localhost', '127.0.0.1']]
            if hosts:
                protocol = "https" if not settings.DEBUG else "http"
                return f"{protocol}://{hosts[0]}{path}"

        # Fallback to localhost for development
        return f"http://localhost:8000{path}"
