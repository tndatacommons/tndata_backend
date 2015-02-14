"""
Django settings for tndata_backend project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

ADMINS = (
    ('Brad Montgomery', 'bkmontgomery@tndata.org'),
)
MANAGERS = ADMINS
DEFAULT_FROM_EMAIL = 'webmaster@tndata.org'
SERVER_EMAIL = 'webmaster@tndata.org'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

SECRET_KEY = 'xt67918srm3f=0$#k%7quk+&pdtwy7#n=pfn%4kzyae$kxmw%j'
DEBUG = False
TEMPLATE_DEBUG = False
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.tndata.org', '.tndata.org.']

TEMPLATE_DIRS = [
    os.path.join(BASE_DIR, 'templates')
]


INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'djorm_pgarray',
    'jsonfield',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'diary',
    'goals',
    'rules',
    'survey',
    'userprofile',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.BrokenLinkEmailsMiddleware',  # Send email on 404
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'tndata_backend.urls'
WSGI_APPLICATION = 'tndata_backend.wsgi.application'

# Production Database settings.
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'tndata_backend',
        'USER': 'tndata_backend',
        'PASSWORD': 'plicater-nonurban-outlaw-moonfall',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

# django.contrib.auth settings.
LOGIN_URL = 'login'  # Named url patter for the built-in auth
LOGOUT_URL = 'logout'
LOGIN_REDIRECT_URL = '/'


# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Chicago'  # default was UTC
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Media Uploads, default
MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')
MEDIA_URL = "/media/"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'collected_static_files')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Messages tags: Updated to represent Foundation alert classes.
from django.contrib.messages import constants as message_constants
MESSAGE_TAGS = {
    message_constants.DEBUG: 'debug secondary',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR: 'error alert'
}

# Django Rest Framework
REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],

    # Makes the api only accessible by admin users
    #'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAdminUser',),
    'PAGINATE_BY': 20,  # Turns on Pagination.

    # the default authentication options. for more info, see:
    # http://www.django-rest-framework.org/api-guide/authentication/
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    )
}


# django-core-headers
# https://github.com/ottoyiu/django-cors-headers/
CORS_ORIGIN_ALLOW_ALL = False
CORS_ORIGIN_WHITELIST = (
    'localhost',
    '127.0.0.1'
)

