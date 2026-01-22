from django.apps import AppConfig


class HomecontentConfig(AppConfig):
    name = 'homecontent'

    def ready(self):
        import homecontent.signals