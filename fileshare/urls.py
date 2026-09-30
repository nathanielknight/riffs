from django.urls import path
from . import views

app_name = "fileshare"

urlpatterns = [
    path("<str:share_key>/", views.serve_file, name="serve"),
]
