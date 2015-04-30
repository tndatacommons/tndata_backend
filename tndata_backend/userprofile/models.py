from collections import defaultdict
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.db.models import ObjectDoesNotExist
from django.dispatch import receiver

from rest_framework.authtoken.models import Token
from survey.models import Instrument


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

    def _response(self, question):
        m = {
            'binaryquestion': 'binaryresponse_set',
            'likertquestion': 'likertresponse_set',
            'multiplechoicequestion': 'multiplechoiceresponse_set',
            'openendedquestion': 'openendedresponse_set'
        }
        return getattr(question, m[question.question_type]).latest()

    @property
    def bio(self):
        # UGH. We shoe-horned this shit into a survey and now there's no
        # clean way to get what *should* be a 1-to-1 relationship between
        # a user an some responses. I'm just hard-coding this for now because
        # i hate future me.
        results = []
        try:
            inst = Instrument.objects.get(pk=4)
            for qtype, question in inst.questions:
                data = {
                    'question_id': question.id,
                    'question_type': question.question_type,
                    'question_text': "{0}".format(question),
                    'response_url': question.get_api_response_url(),
                    'question_url': question.get_survey_question_url(),
                    'response_id': None,
                }
                option_types = [
                    'binaryquestion', 'likertquestion', 'multiplechoicequestion'
                ]
                if question.question_type in option_types:
                    data['selected_option'] = None
                    data['selected_option_text'] = ''
                elif question.question_type == 'openendedquestion':
                    data['response'] = None
                    data['question_input_type'] = question.input_type

                # Fill in any of the user's responses.
                try:
                    r = self._response(question)
                    data['response_id'] = r.id
                    if question.question_type in option_types:
                        data['selected_option'] = r.selected_option.id
                        data['selected_option_text'] = r.selected_option_text
                    elif question.question_type == 'openendedquestion':
                        data['response'] = r.response
                except ObjectDoesNotExist:
                    pass
                results.append(data)

        except Instrument.DoesNotExist:
            pass
        return results

    @property
    def surveys(self):
        """
        # TODO: Figure out what to do with this and if/when we need it (probably
        for users to go back to their survey questions or directly complete
        surveys; it'll need to be re-worked)

        Return a simple representation of the survey questions that the
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
