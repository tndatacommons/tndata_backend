from .base import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG

# django-cors-headers: https://github.com/ottoyiu/django-cors-headers/
CORS_ORIGIN_ALLOW_ALL = False

# EMAIL via Mailgun. Production server details, below (app.tndata.org)
EMAIL_HOST = 'smtp.mailgun.org'
EMAIL_HOST_USER = 'postmaster@app.tndata.org'
EMAIL_HOST_PASSWORD = '29f90e907d425a4a610a558fef85db42'
EMAIL_PORT = '587'
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
