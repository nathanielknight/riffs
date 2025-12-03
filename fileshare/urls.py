from django.urls import path
from . import views

app_name = "fileshare"

urlpatterns = [
    path("<uuid:share_key>", views.serve_file, name="serve"),
]
