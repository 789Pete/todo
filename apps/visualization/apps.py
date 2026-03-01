from django.apps import AppConfig


class VisualizationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.visualization"

    def ready(self):
        import apps.visualization.signals  # noqa: F401
