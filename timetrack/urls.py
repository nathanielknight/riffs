from django.urls import path

from . import views

app_name = "timetrack"

urlpatterns = [
    path("", views.index, name="index"),
    path("weeks", views.weeks, name="weeks"),
    path("weeks/<str:date>", views.week, name="week"),
    path("start", views.start, name="start"),
    path("stop", views.stop, name="stop"),
    path("add", views.add_interval, name="add"),
    path("interval/<int:id>", views.edit_interval, name="edit"),
    path("interval/<int:id>/delete", views.delete_interval, name="delete"),
    path("manifest.webmanifest", views.manifest, name="manifest"),
    path("sw.js", views.service_worker, name="service_worker"),
    path("push/subscribe", views.push_subscribe, name="push_subscribe"),
    path("push/unsubscribe", views.push_unsubscribe, name="push_unsubscribe"),
    path("push/test", views.push_test, name="push_test"),
]
