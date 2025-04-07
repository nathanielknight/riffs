from django.contrib import admin
from .models import Quote


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ("slug", "source", "link", "created_at", "updated_at")
    search_fields = ("slug", "content", "source", "link")
    list_filter = ("created_at", "updated_at")
    ordering = ("-created_at",)
