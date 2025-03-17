from django.urls import path

from . import views

app_name = "bookmarks"

urlpatterns = [
    path("", views.index, name="index"),
    path("bookmark/<int:id>", views.bookmark, name="bookmark"),
    path("tags", views.tag_index, name="tags"),
    path("tag/<int:tagid>", views.tag_detail, name="tag"),
]
