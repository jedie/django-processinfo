from django.apps import AppConfig
from django.conf import settings
from django.core.checks import Error, register


MIDDLEWARE = "django_processinfo.middlewares.ProcessInfoMiddleware"


class DjangoProcessinfoConfig(AppConfig):
    """
    https://docs.djangoproject.com/en/2.0/ref/applications/
    """
    name = 'django_processinfo'
    verbose_name = "Django Processinfo"


@register()
def setup_check(app_configs, **kwargs):
    errors = []

    if MIDDLEWARE not in settings.MIDDLEWARE:
        errors.append(
            Error(
                "Missing middleware!",
                hint=f"Add {MIDDLEWARE!r} to settings.MIDDLEWARE",
                obj=settings,
                id='django_processinfo.apps.setup_check',
            )
        )

    if not hasattr(settings, "PROCESSINFO"):
        errors.append(
            Error(
                "Missing settings.PROCESSINFO !",
                hint="Add 'from django_processinfo import app_settings as PROCESSINFO' into your settings.py",
                obj=settings,
                id='django_processinfo.apps.setup_check',
            )
        )

    return errors
