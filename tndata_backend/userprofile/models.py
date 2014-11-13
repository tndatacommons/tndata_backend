from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """A *profile* for a single user.

    This profile contains information about a user, such as demographic and
    biographical data, that doesn't change frequently.

    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        help_text="The user to whom this profile belongs"
    )
    birthdate = models.DateField(blank=True, null=True)

    # TODO: These should have CHOICEs
    race = models.CharField(max_length=10, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    marital_status = models.CharField(max_length=10, blank=True)
    educational_level = models.CharField(max_length=32, blank=True)

    mobile_phone = models.CharField(max_length=32, blank=True)
    home_phone = models.CharField(max_length=32, blank=True)
    home_address = models.CharField(max_length=32, blank=True)
    home_city = models.CharField(max_length=32, blank=True)
    home_state = models.CharField(max_length=32, blank=True)
    home_zip = models.CharField(max_length=32, blank=True)

    # TODO: There's lots of other potential data here.
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{}".format(self.user)

    class Meta:
        order_with_respect_to = "user"
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


@receiver(post_save, sender=settings.AUTH_USER_MODEL, dispatch_uid='create_userprofile')
def create_userprofile(sender, **kwargs):
    """Create a UserProfile whenever a User is created."""
    if kwargs.get('created', False):
        UserProfile.objects.using(kwargs.get("using", "default")).create(
            user=kwargs.get('instance')
        )
