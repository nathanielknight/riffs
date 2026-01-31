"""
Base AppConfig class for Riffs apps.

This module provides RiffsAppConfig, a Django AppConfig subclass that adds
metadata for Riffs apps to indicate whether they have views and whether they
should be publicly listed.
"""

from django.apps import AppConfig


class RiffsAppConfig(AppConfig):
    """
    Base AppConfig for Riffs apps.

    Attributes:
        has_views (bool): Indicates if the app has web views/UI.
        is_public (bool): Indicates if the app should be publicly listed on the main page.
    """

    # Default values - subclasses should override these
    has_views = False
    is_public = False

    @classmethod
    def get_riffs_apps(cls):
        """
        Get all installed Riffs apps.

        Returns:
            list: List of RiffsAppConfig instances that are installed.
        """
        from django.apps import apps

        riffs_apps = []
        for app_config in apps.get_app_configs():
            if isinstance(app_config, cls):
                riffs_apps.append(app_config)

        return riffs_apps

    @classmethod
    def get_public_apps_with_views(cls):
        """
        Get all public Riffs apps that have views.

        Returns:
            list: List of RiffsAppConfig instances that are public and have views.
        """
        return [
            app for app in cls.get_riffs_apps()
            if app.is_public and app.has_views
        ]
