from django.shortcuts import render
from riffs.riffs_app import RiffsAppConfig


def index(req):
    """
    Main landing page that dynamically lists all public Riffs apps.
    """
    riffs_apps = RiffsAppConfig.get_public_apps_with_views()
    context = {
        'riffs_apps': riffs_apps,
    }
    return render(req, "index.html", context)
