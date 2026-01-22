from django.apps import AppConfig


class SacredSitesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sacredsites"

    def ready(self):
        import sacredsites.signals
