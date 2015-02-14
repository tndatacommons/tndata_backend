from .base import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG

# Static Files/Media Uploads (TODO: put these on s3)
STATIC_URL = '/static/'
MEDIA_ROOT = "/webapps/tndata_backend/uploads/"
MEDIA_URL = "/media/"

# django-core-headers: https://github.com/ottoyiu/django-cors-headers/
CORS_ORIGIN_ALLOW_ALL = False

# EMAIL via Mailgun. Production server details, below (app.tndata.org)
EMAIL_HOST = 'smtp.mailgun.org'
EMAIL_HOST_USER = 'postmaster@app.tndata.org'
EMAIL_HOST_PASSWORD = '29f90e907d425a4a610a558fef85db42'
EMAIL_PORT = '587'
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
