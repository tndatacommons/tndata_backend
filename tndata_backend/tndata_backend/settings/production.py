from .base import *

DEBUG = False

# django-cors-headers: https://github.com/ottoyiu/django-cors-headers/
CORS_ORIGIN_ALLOW_ALL = False

# EMAIL via Mailgun. Production server details, below (app.tndata.org)
EMAIL_HOST = 'smtp.mailgun.org'
EMAIL_HOST_USER = 'postmaster@app.tndata.org'
EMAIL_HOST_PASSWORD = '29f90e907d425a4a610a558fef85db42'
EMAIL_PORT = '587'
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False


# Logging Config
# --------------
# This config is for loggly.com; It should work in addition to the django
# default logging config.
#
# See https://docs.python.org/3/library/logging.handlers.html#sysloghandler
# for information on the SysLogHandler.
LOGGING = {
   'version': 1,
   'disable_existing_loggers': False,
   'formatters': {
      'django': {
         'format':'django: %(message)s',
       },
    },
   'handlers': {
      'logging.handlers.SysLogHandler': {
         'level': 'DEBUG',
         'class': 'logging.handlers.SysLogHandler',
         'facility': 'local7',
         'formatter': 'django',
       },
   },
   'loggers': {
      'loggly_logs':{
         'handlers': ['logging.handlers.SysLogHandler'],
         'propagate': True,
         'format':'django: %(message)s',
         'level': 'DEBUG',
       },
    }
}


# Django Haystack / Elasticsearch
HAYSTACK_CONNECTIONS['default']['URL'] = 'http://worker.tndata.org:9200/'


# -----------------------------------------------------------------------------
# Amazon S3 & django-storages config
# -----------------------------------------------------------------------------

AWS_STORAGE_BUCKET_NAME = "tndata-production"
AWS_BUCKET_NAME = AWS_STORAGE_BUCKET_NAME  # for sync_s3
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, STATICFILES_LOCATION)
MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)

# -----------------------------------------------------------------------------
