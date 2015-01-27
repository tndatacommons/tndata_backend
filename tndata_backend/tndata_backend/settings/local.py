from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
TEMPLATE_DEBUG = True

INSTALLED_APPS = INSTALLED_APPS + (
    'debug_toolbar',
)

# Media Uploads for Development
# NOTE. during dev, cd into uploads and run `serve 8888`
MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')
MEDIA_URL = "/media/"

# django-core-headers
# https://github.com/ottoyiu/django-cors-headers/
CORS_ORIGIN_ALLOW_ALL = True

# Rainbow-tests
TEST_RUNNER = 'rainbowtests.test.runner.RainbowDiscoverRunner'
