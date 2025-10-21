class GamesRouter:
    """
    A router to control all database operations on models in the
    gamesearch application.
    """
    route_app_labels = {"gamesearch"}

    def db_for_read(self, model, **hints):
        """
        Attempts to read gamesearch models go to games db.
        """
        if model._meta.app_label in self.route_app_labels:
            return "games"
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write gamesearch models go to games db.
        """
        if model._meta.app_label in self.route_app_labels:
            return "games"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the gamesearch app is involved.
        """
        if (
            obj1._meta.app_label in self.route_app_labels
            or obj2._meta.app_label in self.route_app_labels
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the gamesearch app only appears in the 'games'
        database.
        """
        if app_label in self.route_app_labels:
            return db == "games"
        return None
