from .base import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG

# Static Files/Media Uploads (TODO: put these on s3)
STATIC_URL = '/static/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')
MEDIA_URL = "/media/"

# django-core-headers: https://github.com/ottoyiu/django-cors-headers/
CORS_ORIGIN_ALLOW_ALL = False
