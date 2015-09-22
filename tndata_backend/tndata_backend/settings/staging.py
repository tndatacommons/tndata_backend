from .base import *

DEBUG = False
STAGING = True

# Site's FQDN and URL. For building links in email.
SITE_DOMAIN = "staging.tndata.org"
SITE_URL = "https://{0}".format(SITE_DOMAIN)

INSTALLED_APPS = INSTALLED_APPS + (
    'debug_toolbar',
    'querycount',
)

# Just like production, but without the cached template loader
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG
TEMPLATES[0]['OPTIONS']['loaders'] = [
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
]

# django-cors-headers: https://github.com/ottoyiu/django-cors-headers/
CORS_ORIGIN_ALLOW_ALL = True

# EMAIL via Mailgun. Production server details, below (staging.tndata.org)
EMAIL_SUBJECT_PREFIX = "[Staging TNData] "
EMAIL_HOST = 'smtp.mailgun.org'
EMAIL_HOST_USER = 'postmaster@staging.tndata.org'
EMAIL_HOST_PASSWORD = '29f90e907d425a4a610a558fef85db42'
EMAIL_PORT = '587'
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

# Rainbow-tests
TEST_RUNNER = 'rainbowtests.test.runner.RainbowDiscoverRunner'

# Explicit setting for debug_toolbar
DEBUG_TOOLBAR_PATCH_SETTINGS = False
MIDDLEWARE_CLASSES = (
    'querycount.middleware.QueryCountMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
) + MIDDLEWARE_CLASSES

INTERNAL_IPS = (
    '159.203.68.206',
    '127.0.0.1',
    '::1',
)
