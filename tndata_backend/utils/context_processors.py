from django.conf import settings


def staging(request):
    """Adds a `staging` context variable when the STAGING settings is True."""
    return {'staging': getattr(settings, 'STAGING', False)}


def site_domain(request):
    """Adds the `settings.SITE_DOMAIN` and `settings.SITE_URL` values to the
    context as `site_domain` and `site_url`."""
    return {
        'site_domain': settings.SITE_DOMAIN,
        'site_url': settings.SITE_URL,
    }
