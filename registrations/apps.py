from django.apps import AppConfig


class RegistrationsConfig(AppConfig):
    name = 'registrations'

    def ready(self):
        import registrations.signals  # noqa
        from django.db.utils import OperationalError, ProgrammingError
        from .services import refresh_all_dashboard_stats, schedule_midnight_refresh

        try:
            refresh_all_dashboard_stats()
            schedule_midnight_refresh()
        except (OperationalError, ProgrammingError):
            # Database might not be ready during initial migrate
            pass
