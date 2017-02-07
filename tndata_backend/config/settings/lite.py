""" These are the *lite* Django settings.

Typically this project would run in a VM, but this file makes it possible to
run on a more resource-constrained machine. However, you'll likely still need
a few bits of infrastructure running:


"""

from .base import *

# --- Import & Override our base settings. ------------------------------------
# NOTE: still need app environment variables set.

# Email: Local email delivery
# python -m smtpd -n -c DebuggingServer localhost:1025
EMAIL_HOST = 'localhost'
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False
EMAIL_PORT = 1025

# For development, we can use a dummy or a local-memory cache.
CACHES = {
    'default': {
        #'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake'
    }
}

# We typically use Redis cache as a session backend, this sets it back to default.
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_CACHE_ALIAS = "default"
