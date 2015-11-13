from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
STAGING = False

SITE_DOMAIN = "localhost"
SITE_URL = "http://127.0.0.1:8000"
MANAGERS = ADMINS

QUERYCOUNT = {
    'THRESHOLDS': {
        'MEDIUM': 50,
        'HIGH': 200,
        'MIN_TIME_TO_LOG': 0,
        'MIN_QUERY_COUNT_TO_LOG': 0
    },
    'IGNORE_PATTERNS': [r'^/static', r'^/media', r'^/admin'],
}


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

# Disable AWS/S3 (for when working on js/css locally)
# ---------------------------------------------------
STATIC_ROOT = "collected_static_files"
STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)
MEDIA_ROOT = "/webapps/tndata_backend/uploads/"
MEDIA_URL = "/media/"
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"


# Caching: Uses defaults from settings.base

# EMAIL via Mailgun.
# Details for the DEV sandbox server:
# sandbox4dc4d62d8cf24785914c55630ab480e6.mailgun.org
EMAIL_HOST = 'smtp.mailgun.org'
EMAIL_HOST_USER = 'postmaster@sandbox4dc4d62d8cf24785914c55630ab480e6.mailgun.org'
EMAIL_HOST_PASSWORD = 'ac2a70a9988127ff7fa217f559c2d59a'
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_PORT = '587'  # 25, 587, 465

# Local email delivery
#EMAIL_HOST = 'localhost'
#EMAIL_HOST_USER = ''
#EMAIL_HOST_PASSWORD = ''
#EMAIL_USE_TLS = False
#EMAIL_PORT = 1025

# django-cors-headers
# https://github.com/ottoyiu/django-cors-headers/
CORS_ORIGIN_ALLOW_ALL = True

# Explicit setting for debug_toolbar
DEBUG_TOOLBAR_PATCH_SETTINGS = False
MIDDLEWARE_CLASSES = (
    'querycount.middleware.QueryCountMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
) + MIDDLEWARE_CLASSES

INTERNAL_IPS = (
    '10.0.2.2',  # The Remote address of the proxied requests.
    '10.0.2.15',
    '192.168.33.10',
    '127.0.0.1',
    '::1',
)
