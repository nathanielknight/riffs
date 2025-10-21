from django.urls import path
from . import views

app_name = "gamesearch"

urlpatterns = [
    path("", views.search_games, name="search"),
]
