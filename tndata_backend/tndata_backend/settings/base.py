""" Django settings for tndata_backend project.

This file expects that the following environment variables are in place:

* ADMIN_NAME
* ADMIN_EMAIL
* MANAGER_NAME
* MANAGER_EMAIL
* DEFAULT_EMAIL

"""

import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Admins & Managers for the site.
ADMINS = [(os.environ.get('ADMIN_NAME'), os.environ.get('ADMIN_EMAIL'))]
MANAGERS = ADMINS + [(os.environ.get('ADMIN_NAME'), os.environ.get('ADMIN_EMAIL'))]

# Email
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_EMAIL')
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_SUBJECT_PREFIX = "[TNData] "

# The site's FQDN and URL. Used for building links in email.
SITE_DOMAIN = os.environ.get('SITE_DOMAIN')
SITE_URL = "https://{0}".format(SITE_DOMAIN)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = False
STAGING = False

# The environment variable for allowed hosts should be a ;-separated string
# of domains and/or ip addresses, e.g. "localhost;127.0.0.1;example.com"
ALLOWED_HOSTS = ";".split(os.environ.get('ALLOWED_HOSTS'))

# NOTE: this is the production setting. It uses the cached.Loader.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates')
        ],
        'OPTIONS': {
            'debug': DEBUG,
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
            'context_processors': (
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.core.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "utils.context_processors.staging",
            ),
        },
    },
]


INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 3rd-party apps
    'cacheops',
    'corsheaders',
    'crispy_forms',
    'crispy_forms_foundation',
    'django_extensions',
    'haystack',
    'jsonfield',
    'recurrence',
    'redis_metrics',
    'rest_framework',
    'rest_framework.authtoken',
    'storages',
    'staticflatpages',
    'waffle',
    # custom apps
    'goals',
    'notifications',
    'rewards',
    'survey',
    'userprofile',
    'utils',
)


# django-haystack settings
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': os.environ.get('HAYSTACK_URL'),
        'INDEX_NAME': os.environ.get('HAYSTACK_INDEX_NAME'),
    },
}


# Settings for Google Cloud Messaging.
GCM = {
    'API_KEY': os.environ.get('GCM_API_KEY'),
}

AUTHENTICATION_BACKENDS = (
    'utils.backends.EmailAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'waffle.middleware.WaffleMiddleware',
    'utils.middleware.TimezoneMiddleware',
    'utils.middleware.ResponseForbiddenMiddleware',
    'staticflatpages.middleware.StaticFlatpageFallbackMiddleware',
)

ROOT_URLCONF = 'tndata_backend.urls'
WSGI_APPLICATION = 'tndata_backend.wsgi.application'

# Local Database settings.
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
    }
}

# Caching with a redis backend
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')
REDIS_PORT = os.environ.get('REDIS_PORT')
REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_CACHE_DB = 1  # XXX Used in production
REDIS_CACHE_URL = 'redis://:{password}@{host}:{port}/{db}'.format(
    password=REDIS_PASSWORD,
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_CACHE_DB
)
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_CACHE_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,  # in seconds
            "SOCKET_TIMEOUT": 5,  # in seconds
        },
        'TIMEOUT': 1200,  # 1-hour cache
    }
}

# django-redis-metrics: http://django-redis-metrics.readthedocs.org/en/latest/
REDIS_METRICS_DB = 2  # XXX Used in production
REDIS_METRICS = {
    'HOST': REDIS_HOST,
    'PORT': REDIS_PORT,
    'DB':  REDIS_METRICS_DB,
    'PASSWORD': REDIS_PASSWORD,
    'SOCKET_TIMEOUT': None,
    'SOCKET_CONNECTION_POOL': None,
    'MIN_GRANULARITY': 'daily',
    'MAX_GRANULARITY': 'yearly',
    'MONDAY_FIRST_DAY_OF_WEEK': False,
}


# Use the Redis cache as a session backend: https://goo.gl/U0xajQ
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_CACHE_ALIAS = "default"

# django-cacheops: https://github.com/Suor/django-cacheops#readme
CACHEOPS_REDIS = {
    'host': REDIS_HOST,
    'port': REDIS_PORT,
    'db': REDIS_CACHE_DB,
    'socket_timeout': 5,
    'password': REDIS_PASSWORD,
}
CACHEOPS_DEFAULTS = {'timeout': 60 * 60}
CACHEOPS = {
    'auth.*': {'ops': ('fetch', 'get')},
    'auth.permission': {'ops': 'all'},
    'goals.*': {'ops': ('fetch', 'get')},
    'userprofile.userprofile': {'ops': ('fetch', 'get')},
}
CACHEOPS_DEGRADE_ON_FAILURE = True


# django.contrib.auth settings.
LOGIN_URL = 'login'  # Named url patter for the built-in auth
LOGOUT_URL = 'logout'
LOGIN_REDIRECT_URL = '/'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
TIME_FORMAT = "g:ia e"  # 5:30pm CDT
DATE_FORMAT = "N j, Y"  # Jan 3, 2015
DATETIME_FORMAT = "N j, Y g:iaO e"  # Jan. 3, 2015 5:30pm+200 CDT
SHORT_DATE_FORMAT = "m/d/Y"  # 01/03/2015
SHORT_DATETIME_FORMAT = "H:iO"  # 17:30+200
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Messages tags: Updated to represent Foundation alert classes.
from django.contrib.messages import constants as message_constants
MESSAGE_TAGS = {
    message_constants.DEBUG: 'debug secondary',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR: 'error alert'
}

# Rainbow-tests
TEST_RUNNER = 'rainbowtests.test.runner.RainbowDiscoverRunner'


# Crispy forms
CRISPY_TEMPLATE_PACK = 'foundation-5'
CRISPY_ALLOWED_TEMPLATE_PACKS = ('uni_form', 'foundation-5')

# Django Rest Framework
REST_FRAMEWORK = {
    'PAGINATE_BY': 100,
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'utils.api.BrowsableAPIRendererWithoutForms',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/day',
        'user': '10000/day'
    },
}


# Play Store Link for the mobile app.
# https://developers.google.com/api-client-library/python/start/get_started
PLAY_APP_URL = os.environ.get('PLAY_APP_URL')

# django-cors-headers: https://github.com/ottoyiu/django-cors-headers/
CORS_ORIGIN_ALLOW_ALL = False
CORS_ORIGIN_WHITELIST = (
    'localhost',
    '127.0.0.1'
)


# Slack tokens: https://api.slack.com/web
SLACK_API_TOKEN = os.environ.get('SLACK_API_TOKEN')
SLACK_CHANNEL = os.environ.get('SLACK_CHANNEL')
SLACK_USERNAME = os.environ.get('SLACK_USERNAME')

# Media Uploads, default
MEDIA_ROOT = os.environ.get('MEDIA_ROOT')

# Static files (CSS, JavaScript, Images)
STATIC_ROOT = os.path.join(BASE_DIR, 'collected_static_files')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]


# Amazon S3 & django-storages config
AWS_USER = os.environ.get('AWS_USER')
AWS_HEADERS = {  # http://developer.yahoo.com/performance/rules.html#expires
    'Expires': 'Thu, 31 Dec 2099 20:00:00 GMT',
    'Cache-Control': 'max-age=94608000',
}
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_BUCKET_NAME = AWS_STORAGE_BUCKET_NAME  # for sync_s3
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
SYNC_S3_PREFIX = 'media'  # only include our media files when using sync_s3

# Tell django-storages that when coming up with the URL for an item in S3
# storage, keep it simple - just use this domain plus the path. (If this isn't
# set, things get complicated). This controls how the `static` template tag
# from `staticfiles` gets expanded, if you're using it.
#
# We also use it in the next setting.
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

# Tell the staticfiles app to use S3Boto storage when writing the collected
# static files (when you run `collectstatic`).
STATICFILES_LOCATION = 'static'
STATICFILES_STORAGE = 'utils.storages.StaticStorage'

# This is used by the `static` template tag from `static`, if you're using that.
# Or if anything else refers directly to STATIC_URL. So it's safest to always
# set it.
STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, STATICFILES_LOCATION)

MEDIAFILES_LOCATION = 'media'
MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)
DEFAULT_FILE_STORAGE = 'utils.storages.MediaStorage'

# Additional Goal app Settings
PROGRESS_HISTORY_DAYS = 30  # Number of days back to generate progress history
