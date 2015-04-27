from collections import defaultdict
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from rest_framework.authtoken.models import Token


class UserProfile(models.Model):
    """A *profile* for a single user.

    This profile contains information about a user, such as demographic and
    biographical data, that doesn't change frequently.

    Bio-8: Storing answers to 8 biographical questions: http://goo.gl/CSzRZp

    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        help_text="The user to whom this profile belongs"
    )
    # TODO: REMOVE the following profile-like fields; we get those from surveys.
    birthdate = models.DateField(blank=True, null=True, db_index=True)
    race = models.CharField(max_length=128, blank=True, db_index=True)
    gender = models.CharField(max_length=128, blank=True, db_index=True)

    relationship_status = models.CharField(max_length=128, blank=True)
    educational_level = models.CharField(max_length=128, blank=True)
    employment_status = models.CharField(max_length=128, blank=True)
    children = models.CharField(max_length=128, blank=True)
    economic_aspiration = models.CharField(max_length=128, blank=True)

    mobile_phone = models.CharField(max_length=32, blank=True)
    home_phone = models.CharField(max_length=32, blank=True)
    home_address = models.CharField(max_length=32, blank=True)
    home_city = models.CharField(max_length=32, blank=True)
    home_state = models.CharField(max_length=32, blank=True)
    home_zip = models.CharField(max_length=32, blank=True)

    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{}".format(self.user)

    class Meta:
        order_with_respect_to = "user"
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    @property
    def surveys(self):
        """Return a simple representation of the survey questions that the
        user has answered.

        """
        # NOTE: I'm not sure what the best approach is, here, because our
        # questions are M2M fields under Instruments; That means there's possibly
        # no 1-to-1 relationship between a User's response and the instrument
        # in which it's placed.

        # Get all the questions & return a dict of primitive types
        # (dicts & lists; so it's easy to serialize)
        surveys = defaultdict(list)
        for resp in self.user.binaryresponse_set.all():
            for inst in resp.question.instruments.all():
                surveys[inst.id].append({
                    'id': resp.id,
                    'instrument': {
                        "id": inst.id,
                        "title": "{0}".format(inst),
                    },
                    'question_id': resp.question.id,
                    'question_type': resp.question.question_type,
                    'question_text': "{0}".format(resp.question),
                    'selected_option': resp.selected_option,
                })
        for resp in self.user.openendedresponse_set.all():
            for inst in resp.question.instruments.all():
                surveys[inst.id].append({
                    'id': resp.id,
                    'instrument': {
                        "id": inst.id,
                        "title": "{0}".format(inst),
                    },
                    'question_id': resp.question.id,
                    'question_text': "{0}".format(resp.question),
                    'question_type': resp.question.question_type,
                    'response': resp.response,
                })
        for resp in self.user.likertresponse_set.all():
            for inst in resp.question.instruments.all():
                surveys[inst.id].append({
                    'id': resp.id,
                    'instrument': {
                        "id": inst.id,
                        "title": "{0}".format(inst),
                    },
                    'question_id': resp.question.id,
                    'question_text': "{0}".format(resp.question),
                    'question_type': resp.question.question_type,
                    'selected_option': resp.selected_option,
                })
        for resp in self.user.multiplechoiceresponse_set.all():
            for inst in resp.question.instruments.all():
                surveys[inst.id].append({
                    'id': resp.id,
                    'instrument': {
                        "id": inst.id,
                        "title": "{0}".format(inst),
                    },
                    'question_id': resp.question.id,
                    'question_text': "{0}".format(resp.question),
                    'question_type': resp.question.question_type,
                    'selected_option': {
                        "id": resp.selected_option.id,
                        "text": resp.selected_option.text,
                    },
                    'selected_option_text': resp.selected_option.text,
                })
        return dict(surveys)


@receiver(post_save, sender=settings.AUTH_USER_MODEL, dispatch_uid='create_userprofile')
def create_userprofile(sender, **kwargs):
    """Create a UserProfile whenever a User is created."""
    if kwargs.get('created', False) and 'instance' in kwargs:
        user = kwargs['instance']

        # Create the user profile.
        UserProfile.objects.using(kwargs.get("using", "default")).create(
            user=user
        )


@receiver(post_save, sender=settings.AUTH_USER_MODEL, dispatch_uid='create_usertoken')
def create_usertoken(sender, **kwargs):
    """All newly-created Users should also get an API token."""
    if kwargs.get('created', False) and 'instance' in kwargs:
        Token.objects.create(user=kwargs['instance'])
