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
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}


INSTALLED_APPS = INSTALLED_APPS + (
    'debug_toolbar',
)

# django-core-headers
# https://github.com/ottoyiu/django-cors-headers/
CORS_ORIGIN_ALLOW_ALL = True

# Rainbow-tests
TEST_RUNNER = 'rainbowtests.test.runner.RainbowDiscoverRunner'
