from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# TODO: Add querycount settings to ignore: admin, static files
QUERYCOUNT = {
    'THRESHOLDS': {
        'MEDIUM': 50,
        'HIGH': 200,
        'MIN_TIME_TO_LOG':0,
        'MIN_QUERY_COUNT_TO_LOG':0
    },
    'IGNORE_PATTERNS': [r'^/static', r'^/media', r'^/admin'],
}


INSTALLED_APPS = INSTALLED_APPS + (
    'debug_toolbar',
    'querycount',
)

# Exclude the cached.Loader from dev so we render the template each time.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': (
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.tz",
            ),
        },
    },
]

# Media Uploads for Development
MEDIA_ROOT = "/webapps/tndata_backend/uploads/"
MEDIA_URL = "/media/"
STATIC_URL = "/static/"

# EMAIL via Mailgun.
# Details for the DEV sandbox server:
# sandbox4dc4d62d8cf24785914c55630ab480e6.mailgun.org
EMAIL_HOST = 'smtp.mailgun.org'
EMAIL_HOST_USER = 'postmaster@sandbox4dc4d62d8cf24785914c55630ab480e6.mailgun.org'
EMAIL_HOST_PASSWORD = 'ac2a70a9988127ff7fa217f559c2d59a'
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_PORT = '587'  # 25, 587, 465

# django-cors-headers
# https://github.com/ottoyiu/django-cors-headers/
CORS_ORIGIN_ALLOW_ALL = True

# Rainbow-tests
TEST_RUNNER = 'rainbowtests.test.runner.RainbowDiscoverRunner'

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
