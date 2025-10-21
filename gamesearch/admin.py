from django.contrib import admin
from .models import RawGame, Star


@admin.register(RawGame)
class RawGameAdmin(admin.ModelAdmin):
    list_display = ("title", "authors", "tags", "is_starred")
    search_fields = ("title", "authors", "tags")
    list_filter = ("tags",)


@admin.register(Star)
class StarAdmin(admin.ModelAdmin):
    list_display = ("gameid",)
    search_fields = ("gameid",)
