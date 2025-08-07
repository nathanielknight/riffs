from django.urls import path
from . import views

app_name = "dropfeed"

urlpatterns = [
    path("", views.index, name="index"),
    path("feed/<str:path>/", views.feed, name="feed"),
    path("recording/<uuid:id>", views.recording, name="recording"),
]
