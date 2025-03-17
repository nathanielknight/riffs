from django.contrib import admin

from .models import Bookmark


@admin.register(Bookmark)
class BookmarksManager(admin.ModelAdmin):
    list_display = ["name", "url", "created_at", "updated_at"]
    readonly_fields = ["created_at", "updated_at"]
