from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
TEMPLATE_DEBUG = True

DATABASES = {  # NOTE: Currently requires Postgresql.app to be running.
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'tndata',
        'USER': 'brad',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

MIDDLEWARE_CLASSES += (
    'tndata_backend.middleware.PolymerDevMiddleware',
)

INSTALLED_APPS = INSTALLED_APPS + (
    'debug_toolbar',
)

# django-core-headers
# https://github.com/ottoyiu/django-cors-headers/
CORS_ORIGIN_ALLOW_ALL = True
