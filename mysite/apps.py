from django.apps import AppConfig

class MySiteConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mysite"

    def ready(self):
        print("🚀 MySiteConfig ready() called!")
        try:
            from . import signals
            print("✅ signals.py imported successfully!")
        except Exception as e:
            print(f"❌ Failed to import signals.py: {e}")