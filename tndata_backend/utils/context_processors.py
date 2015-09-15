from django.conf import settings


def staging(request):
    """Adds a `staging` context variable when the STAGING settings is True."""
    return {'staging': getattr(settings, 'STAGING', False)}
