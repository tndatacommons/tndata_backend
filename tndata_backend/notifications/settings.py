"""
Attempt to pull settings from the project, but specify some defaults.

"""
from django.conf import settings as project_settings
from django.core.exceptions import ImproperlyConfigured

# Attempt to pull settings from the project
gcm_settings = getattr(project_settings, 'GCM', {})


GCM = {
    'API_KEY': gcm_settings.get('API_KEY', None),
}

if GCM['API_KEY'] is None:
    raise ImproperlyConfigured(
        "This app requires an GCM API key. Please specify a GCM.API_KEY setting."
    )


DEFAULTS = getattr(project_settings, 'NOTIFICATIONS', {})
if DEFAULTS.get('DEFAULT_TITLE') is None:
    DEFAULTS['DEFAULT_TITLE'] = "Stay On Course"
if DEFAULTS.get('DEFAULT_TEXT') is None:
    DEFAULTS['DEFAULT_TEXT'] = "Check in with Compass to stay on track toward your goals"
