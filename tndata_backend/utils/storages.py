"""
Custom storage backends to separate Satic files and Media Files (uploaded
by users).

Inspired by: https://goo.gl/xxwxuK

"""
from django.conf import settings
from storages.backends.s3boto import S3BotoStorage


class StaticStorage(S3BotoStorage):
    """An S3 backend storage for static files."""
    location = settings.STATICFILES_LOCATION


class MediaStorage(S3BotoStorage):
    """An S3 backend storage for media (user-uploaded) files."""
    location = settings.MEDIAFILES_LOCATION
