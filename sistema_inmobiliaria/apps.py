from django.apps import AppConfig


class SistemaInmobiliariaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sistema_inmobiliaria'
    
    def ready(self):
        import sistema_inmobiliaria.signals
