from .base import *

DEBUG = False
#DEBUG = True
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
EMAIL_HOST_USER = 'postmaster@sandbox4dc4d62d8cf24785914c55630ab480e6.mailgun.org'
EMAIL_HOST_PASSWORD = 'ac2a70a9988127ff7fa217f559c2d59a'
EMAIL_PORT = '587'
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False


# Caching
# Redis notes: redis_max_clients: 10000, edis_max_memory: 512mb
REDIS_PASSWORD = 'VPoDYBZgeyktxArddu4EHrNMdFsUzf7TtFKTP'
REDIS_HOST = 'worker.tndata.org'
REDIS_CACHE_DB = 2
REDIS_CACHE_URL = 'redis://:{password}@{host}:{port}/{db}'.format(
    password=REDIS_PASSWORD,
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_CACHE_DB
)
CACHES['default']['LOCATION'] = REDIS_CACHE_URL
CACHES['default']['OPTIONS']['IGNORE_EXCEPTIONS'] = True

# django-haystack settings for staging
HAYSTACK_CONNECTIONS['default']['URL'] = 'http://worker.tndata.org:9200/'
HAYSTACK_CONNECTIONS['default']['INDEX_NAME'] = 'haystack_staging'

# django-cacheops
CACHEOPS_REDIS = {
    'host': REDIS_HOST,
    'port': REDIS_PORT,
    'db': REDIS_CACHE_DB,
    'socket_timeout': 5,
    'password': REDIS_PASSWORD,
}


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
