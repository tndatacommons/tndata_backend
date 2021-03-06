"""
Attempt to pull settings from the project, but specify some defaults.

"""
from django.conf import settings as project_settings
from django.core.exceptions import ImproperlyConfigured

# Attempt to pull settings from the project
gcm_settings = getattr(project_settings, 'GCM', {})

GCM = {
    'API_KEY': gcm_settings.get('API_KEY', None),
    'IOS_API_KEY': gcm_settings.get('IOS_API_KEY', None),
}

if GCM['API_KEY'] is None:
    raise ImproperlyConfigured(
        "This app requires an GCM API key. Please specify a GCM.API_KEY setting."
    )


APNS_CERT_PATH = getattr(project_settings, 'APNS_CERT_PATH', None)
if APNS_CERT_PATH is None:
    raise ImproperlyConfigured(
        "This app requires an APNS Certificate. Please specify a APNS_CERT_PATH setting."
    )
