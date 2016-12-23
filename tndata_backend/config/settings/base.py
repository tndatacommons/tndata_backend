""" Django settings file this project.

This file contains settings that are usable for both a production and a
development environment. You'll need to export the appropriate values as
environment variables, however. The following environment variables should
be set prior to running the project:

* DEBUG -- 1 or 0, defines whether or not we're in debug mode.
* STAGING -- 1 or 0, defines whether or not we're in a staging environment.
* SECRET_KEY -- string to use for django's secret key
* ADMIN_NAME -- Name of the admin user.
* ADMIN_EMAIL -- Email of the admin user.
* MANAGER_NAME -- Name of a Manager.
* MANAGER_EMAIL -- Email of a Manager
* DEFAULT_EMAIL -- Default email address for transactional email.
* EMAIL_SUBJECT_PREFIX -- prefix for your emails
* EMAIL_HOST -- host of your smtp server
* EMAIL_HOST_USER -- smtp user
* EMAIL_HOST_PASSWORD -- email password
* EMAIL_USE_TLS -- whether or not to use TLS
* EMAIL_USE_SSL -- whether or not to use SSL
* EMAIL_PORT -- smtp server port
* ALLOWED_HOSTS -- semicolon-separated string of allowed hosts, e.g.
                   "localhost;127.0.0.1;.example.com"
* SITE_DOMAIN -- fully qualified domain name for your site, e.g. "example.com"
* HAYSTACK_URL -- connection to haystack; e.g. "http://127.0.0.1:9200/"
* HAYSTACK_INDEX_NAME -- index name to use for haystack
* GCM_API_KEY -- API key for google cloud messaging
* GCM_IOS_API_KEY -- API key for google cloud messaging (for iOS)
* GOOGLE_OAUTH_CLIENT_ID -- API key for OAuth with Google
* GOOGLE_OAUTH_CLIENT_SECRET -- Secret for OAuth with Google
* ANDROID_OAUTH_CLIENT_ID -- Same as `GOOGLE_OAUTH_CLIENT_ID`, but the ID we're
                             using on the Android app.
* IOS_OAUTH_CLIENT_ID -- Same as `GOOGLE_OAUTH_CLIENT_ID`, but the ID we're
                         using on the iOS app.
* APNS_CERT_PATH  -- Path the the Apple Certificate for APNS
* DB_NAME -- Database name
* DB_USER -- Database user
* DB_PASSWORD -- database password
* DB_HOST -- database host
* DB_PORT -- database port
* REDIS_PASSWORD -- Redis password
* REDIS_PORT -- Redis port
* REDIS_HOST -- Redis host, e.g. "127.0.0.1"
* REDIS_CACHE_DB -- The redis DB to use for the cache.
* REDIS_METRICS_DB -- The redis DB to use for metrics.
* REDIS_RQ_DB -- The redis DB to use for rq task queues.

    - prod / rq         --> 0
    - prod / cache      --> 1
    - prod / metrics    --> 2
    - staging / cache   --> 3
    - staging / metrics --> 4
    - staging / rq      --> 5

* PLAY_APP_URL -- Link to the downloadable app on the play store.
* IOS_APP_URL -- Link to the downloadable app on the apple app store.
* SLACK_API_TOKEN -- slack api token
* SLACK_CHANNEL -- chanel in which you want slack to post e.g. "#general"
* SLACK_USERNAME -- username that will be used for posts to slack
* MEDIA_ROOT -- path to your media uploads (only for local dev if AWS is not used)
* AWS_USER -- AWS user
* AWS_STORAGE_BUCKET_NAME -- S3 bucket name
* AWS_ACCESS_KEY_ID -- AWS access key
* AWS_SECRET_ACCESS_KEY -- AWS secret

"""

from ipaddress import IPv4Network, IPv4Address
import os
import sys


class CIDRS(list):
    """Use the ipaddress module to create lists of ip networks that we check
    against.

        e.g. INTERNAL_IPS = CIDR_LIST(['127.0.0.1', '192.168.0.0/16'])

    Inspired by https://djangosnippets.org/snippets/1862/

    """
    def __init__(self, cidrs):
        self.cidrs = []
        for cidr in cidrs:
            self.cidrs.append(IPv4Network(cidr))

    def __contains__(self, ip):
        # in dev, we get this weird input, where IP is "b''".
        # this hack is a fix for that.
        if len(ip) < 7:
            return True
        return any([IPv4Address(ip) in net for net in self.cidrs])


SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = bool(int(os.environ.get('DEBUG', 1)))

STAGING = bool(int(os.environ.get('STAGING', 0)))
TESTING = sys.argv[1:2] == ['test']
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Admins & Managers for the site.
ADMINS = [(os.environ.get('ADMIN_NAME'), os.environ.get('ADMIN_EMAIL'))]
MANAGERS = ADMINS + [(os.environ.get('ADMIN_NAME'), os.environ.get('ADMIN_EMAIL'))]

# Email
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_EMAIL')
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_SUBJECT_PREFIX = os.environ.get('EMAIL_SUBJECT_PREFIX')
if os.environ.get('EMAIL_HOST'):
    # 3rd-party email delivery.
    EMAIL_HOST = os.environ.get('EMAIL_HOST')
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
    EMAIL_USE_TLS = bool(int(os.environ.get('EMAIL_USE_TLS', 1)))
    EMAIL_USE_SSL = bool(int(os.environ.get('EMAIL_USE_SSL', 0)))
    EMAIL_PORT = os.environ.get('EMAIL_PORT')
else:
    # Local email delivery
    EMAIL_HOST = 'localhost'
    EMAIL_HOST_USER = ''
    EMAIL_HOST_PASSWORD = ''
    EMAIL_USE_TLS = False
    EMAIL_PORT = 1025

# The site's FQDN and URL. Used for building links in email.
SITE_DOMAIN = os.environ.get('SITE_DOMAIN')
if DEBUG:
    SITE_URL = "http://{0}".format(SITE_DOMAIN)
else:
    SITE_URL = "https://{0}".format(SITE_DOMAIN)

# The environment variable for allowed hosts should be a ;-separated string
# of domains and/or ip addresses, e.g. "localhost;127.0.0.1;example.com"
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(";")

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
                "utils.context_processors.site_domain",
                "utils.context_processors.google_client_id",
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
    # 'axes',
    'badgify',
    'badgify_api',
    'channels',
    'corsheaders',
    'crispy_forms',
    'crispy_forms_foundation',
    'cronlog',
    'dashboard',
    'django_extensions',
    'django_rq',
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
    'chat',
    'goals',
    'notifications',
    'officehours',
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

# Google OAuth
GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
ANDROID_OAUTH_CLIENT_ID = os.environ.get('ANDROID_OAUTH_CLIENT_ID')
IOS_OAUTH_CLIENT_ID = os.environ.get('IOS_OAUTH_CLIENT_ID')

# Settings for Google Cloud Messaging.
GCM = {
    'API_KEY': os.environ.get('GCM_API_KEY'),
    'IOS_API_KEY': os.environ.get('GCM_IOS_API_KEY'),
}

# Settings for APNS
APNS_CERT_PATH = os.environ.get('APNS_CERT_PATH')

AUTHENTICATION_BACKENDS = (
    'utils.backends.EmailAuthenticationBackend',
    'utils.backends.EmailAndTokenBackend',
    'django.contrib.auth.backends.ModelBackend',
)

MIDDLEWARE_CLASSES = (
    'utils.middleware.IgnoreRequestMiddleware',
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
    'utils.middleware.APIMetricsMiddleware',
    'staticflatpages.middleware.StaticFlatpageFallbackMiddleware',
    'utils.middleware.DebugMedia404Middleware',
)

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

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
CACHE_TIMEOUT = 60 * 5  # 5-minute cache timeout
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')
REDIS_PORT = os.environ.get('REDIS_PORT')
REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_CACHE_DB = int(os.environ.get('REDIS_CACHE_DB'))
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
            "IGNORE_EXCEPTIONS": not DEBUG,  # True in production
        },
        'TIMEOUT': CACHE_TIMEOUT,
    }
}
if DEBUG:
    # For development, we can use a dummy or a local-memory cache.
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

# django-redis-metrics: http://django-redis-metrics.readthedocs.org/en/latest/
REDIS_METRICS_DB = int(os.environ.get('REDIS_METRICS_DB'))
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


# channels config
REDIS_CHANNELS_URL = 'redis://:{password}@{host}:{port}/0'.format(
    password=REDIS_PASSWORD,
    host=REDIS_HOST,
    port=REDIS_PORT,
)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "asgi_redis.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(REDIS_CHANNELS_URL)],
        },
        "ROUTING": "config.routing.channel_routing",
    },
    # "default": {
        # "BACKEND": "asgiref.inmemory.ChannelLayer",
        # "ROUTING": "config.routing.channel_routing",
    # },
}

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
RAINBOWTESTS_HIGHLIGHT_PATH = '/vagrant/tndata_backend/'
RAINBOWTESTS_SHOW_MESSAGES = False

# django-axes
# AXES_LOGIN_FAILURE_LIMIT = 1
# AXES_LOCK_OUT_AT_FAILURE = False  # Don't lock accounts.
# AXES_VERBOSE = True
# AXES_USERNAME_FORM_FIELD = 'email'

# rq & django_rq config, See:
# - http://python-rq.org/docs/workers/
# - https://github.com/ui/django-rq
# NOTE: To run the worker, do: python manage.py rqworker default
REDIS_RQ_DB = int(os.environ.get('REDIS_RQ_DB'))
RQ_QUEUES = {
    'default': {
        'HOST': REDIS_HOST,
        'PORT': REDIS_PORT,
        'DB': REDIS_RQ_DB,
        'PASSWORD': REDIS_PASSWORD,
        'DEFAULT_TIMEOUT': 360,
        'ASYNC': False if DEBUG else True
    },
}


# Crispy forms
CRISPY_TEMPLATE_PACK = 'foundation-5'
CRISPY_ALLOWED_TEMPLATE_PACKS = ('uni_form', 'foundation-5', 'mdl')

# Django Rest Framework
REST_FRAMEWORK = {
    'PAGE_SIZE': 25,
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
    'VERSION_PARAM': 'version',
    'DEFAULT_VERSION': '2',
    'ALLOWED_VERSIONS': ['1', '2'],
    'DEFAULT_VERSIONING_CLASS': 'utils.api.DefaultQueryParamVersioning',
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S%z',  # 2015-04-28 03:47:25+0000
}


# Play Store Link for the mobile app.
# https://developers.google.com/api-client-library/python/start/get_started
PLAY_APP_URL = os.environ.get('PLAY_APP_URL')
IOS_APP_URL = os.environ.get('IOS_APP_URL')

# django-cors-headers: https://github.com/ottoyiu/django-cors-headers/
CORS_ORIGIN_ALLOW_ALL = False
CORS_URLS_REGEX = r'^/api/.*$'
CORS_ORIGIN_WHITELIST = (
    'app.tndata.org',
    'staging.tndata.org',
    'tndata.ngrok.io',
    'brad.ngrok.io',
    'localhost',
    '127.0.0.1',
)

# Ignore these bad host headers; This circumvents the SuspiciousOperation
# exceptions that would otherwise get raised.
IGNORE_BAD_HOST_HEADERS = [
    'proxyradar.com',  # Stupid check.proxyradar.com/azenv.php
]


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
MEDIAFILES_LOCATION = 'media'
STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, STATICFILES_LOCATION)
MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)
DEFAULT_FILE_STORAGE = 'utils.storages.MediaStorage'

# Additional Goal app Settings
PROGRESS_HISTORY_DAYS = 30  # Number of days back to generate progress history

# django-querycount settings
QUERYCOUNT = {
    'THRESHOLDS': {
        'MEDIUM': 50,
        'HIGH': 200,
        'MIN_TIME_TO_LOG': 0,
        'MIN_QUERY_COUNT_TO_LOG': 0
    },
    'IGNORE_PATTERNS': [r'^/static', r'^/media', r'^/admin'],
    'DISPLAY_DUPLICATES': 1,
}

# Settings for DEBUG / local development
# --------------------------------------
if DEBUG:
    INSTALLED_APPS = INSTALLED_APPS + (
        'debug_toolbar',
        'querycount',
    )

    # django-cors-headers: https://github.com/ottoyiu/django-cors-headers/
    CORS_ORIGIN_ALLOW_ALL = True

    # debug_toolbar
    # -------------
    DEBUG_TOOLBAR_PATCH_SETTINGS = False  # Do not adjust settings automatically
    DEBUG_TOOLBAR_PANELS = [
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
    ]
    MIDDLEWARE_CLASSES = (
        'querycount.middleware.QueryCountMiddleware',
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    ) + MIDDLEWARE_CLASSES
    INTERNAL_IPS = CIDRS(['127.0.0.1', '192.168.0.0/16', '10.0.0.0/16'])

    # Just like production, but without the cached template loader
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


# Logging Config
# --------------

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'django': {
            'format': 'django: %(message)s',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        # 'logging.handlers.SysLogHandler': {
        #    'level': 'DEBUG',
        #    'class': 'logging.handlers.SysLogHandler',
        #    'facility': 'local7',
        #    'formatter': 'django',
        # },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'slack-error': {
            'level': 'ERROR',
            'api_key': SLACK_API_TOKEN,
            'class': 'slacker_log_handler.SlackerLogHandler',
            'channel': '#logs',
            'username': SITE_DOMAIN,
        },
        'slack-info': {
            'level': 'INFO',
            'api_key': SLACK_API_TOKEN,
            'class': 'slacker_log_handler.SlackerLogHandler',
            'channel': '#logs',
            'username': SITE_DOMAIN,
        },
    },
    'loggers': {
        # 'loggly_logs': {
        #    'handlers': ['logging.handlers.SysLogHandler'],
        #    'propagate': True,
        #    'format': 'django: %(message)s',
        #    'level': 'DEBUG',
        # },
        'django.request': {
            'handlers': ['mail_admins', 'slack-error', 'slack-info'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

if DEBUG:
    # No logging in dev
    LOGGING = {}
