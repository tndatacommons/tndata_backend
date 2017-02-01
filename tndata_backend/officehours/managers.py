from django.db import models
from django.utils import timezone


class ExpiresOnManager(models.Manager):
    """A model manager for objects with an `expires_on` field. This manager
    adds methods that let us exclude/filter any expired data.

    """

    def expired(self):
        """Return a queryset of objects that *have* expired."""
        return self.get_queryset().filter(expires_on__lt=timezone.now())

    def current(self, **kwargs):
        """Return a queryset of objects that have not expired."""
        return self.get_queryset().filter(expires_on__gte=timezone.now())
