"""
WSGI config for tndata_backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

import os

# Check to see if we have an environment variable defining the settings,
# and if not, set a default.
if os.environ.get("DJANGO_SETTINGS_MODULE") is None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tndata_backend.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
