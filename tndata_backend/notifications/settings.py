"""
Attempt to pull settings from the project, but specify some defaults.

"""
from django.conf import settings as project_settings
from django.core.exceptions import ImproperlyConfigured

# Attempt to pull settings from the project
gcm_settings = getattr(project_settings, 'GCM', {})


GCM = {
    'API_KEY': gcm_settings.get('API_KEY', None),
    'URL': gcm_settings.get('URL', 'https://android.googleapis.com/gcm/send'),
    'MAX_RECIPIENTS': gcm_settings.get('MAX_RECIPIENTS', 1000),
}

if GCM['API_KEY'] is None:
    raise ImproperlyConfigured(
        "This app requires an GCM API key. Please specify a GCM.API_KEY setting."
    )
