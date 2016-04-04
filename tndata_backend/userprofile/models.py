import pytz

from collections import defaultdict
from datetime import datetime

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save
from django.db.models import ObjectDoesNotExist
from django.dispatch import receiver
from django.utils.text import slugify

from rest_framework.authtoken.models import Token
from survey.models import Instrument


class Place(models.Model):
    name = models.CharField(max_length=32, unique=True, db_index=True)
    slug = models.SlugField(max_length=32, unique=True, db_index=True)

    # We'll let users add their own places, but we want to indicate that
    # some are used for suggestions or as primary places
    primary = models.BooleanField(
        default=False,
        help_text="Use this place as a suggestion for users."
    )

    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{}".format(self.name)

    class Meta:
        ordering = ['name']
        verbose_name = "Place"
        verbose_name_plural = "Places"

    def _format_name(self):
        self.name = self.name.title()
        self.name = "{}{}".format(  # fix for the `Joe'S` bug
            self.name[:-1],
            self.name[-1].lower()
        )

    def _format_slug(self):
        self.slug = slugify(self.name)

    def save(self, *args, **kwargs):
        self._format_name()
        self._format_slug()
        super().save(*args, **kwargs)


class UserPlace(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    profile = models.ForeignKey('UserProfile')
    place = models.ForeignKey(Place)
    latitude = models.DecimalField(max_digits=8, decimal_places=4, db_index=True)
    longitude = models.DecimalField(max_digits=8, decimal_places=4, db_index=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{0} ({1}, {2})".format(self.place, self.latitude, self.longitude)

    class Meta:
        unique_together = ('user', 'place')
        order_with_respect_to = "user"
        verbose_name = "User Place"
        verbose_name_plural = "User Places"

    @property
    def latlon(self):
        return (self.latitude, self.longitude)


class UserProfile(models.Model):
    """A *profile* for a single user; This model contains additional info
    about a user or their account. It also serves as a way to aggregate and
    expose some data for a user.

    """
    SEX_CHOICES = (
        ('female', 'Female'),
        ('male', 'Male'),
        ('no-answer', 'Prefer not to answer'),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        help_text="The user to whom this profile belongs"
    )
    timezone = models.CharField(
        max_length=64,
        default="America/Chicago",
        blank=True,
        choices=[(tz, tz) for tz in pytz.all_timezones]
    )
    maximum_daily_notifications = models.IntegerField(default=10, blank=True)
    needs_onboarding = models.BooleanField(default=True, blank=True)

    # Profile fields.
    zipcode = models.CharField(max_length=32, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    sex = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        choices=SEX_CHOICES
    )
    employed = models.BooleanField(default=False, blank=True)
    is_parent = models.BooleanField(default=False, blank=True)
    in_relationship = models.BooleanField(default=False, blank=True)
    has_degree = models.BooleanField(default=False, blank=True)

    # Timestamps
    updated_on = models.DateTimeField(auto_now=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{}".format(self.user)

    class Meta:
        order_with_respect_to = "user"
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def set_needs_onboarding(self, save=True):
        self.needs_onboarding = True
        if save:
            self.save()

    def get_absolute_url(self):
        return reverse("userprofile:detail", args=[self.pk])

    def get_update_url(self):
        return reverse("userprofile:update", args=[self.pk])

    def _response(self, question):
        """Given a Question, return the user's latest response."""
        m = {
            'binaryquestion': 'binaryresponse_set',
            'likertquestion': 'likertresponse_set',
            'multiplechoicequestion': 'multiplechoiceresponse_set',
            'openendedquestion': 'openendedresponse_set'
        }
        # Get the responses for the given type of question, then filter
        # those for the current user, and return the latest
        responses = getattr(question, m[question.question_type])
        return responses.filter(user=self.user).latest()

    def _get_bio_responses(self, question_type, question_id):
        qid = 'question_id'
        qtype = 'question_type'
        return [
            d for d in self.bio
            if d[qid] == question_id and d[qtype] == question_type
        ]

    def _get_profile_survey_responses(self, question_type, question_id):
        qid = 'question_id'
        qtype = 'question_type'
        return [
            d for d in self.profile_survey
            if d[qid] == question_id and d[qtype] == question_type
        ]

    # -------------------------------------------------------------------------
    # Bio/Onboarding survey responses.
    # -------------------------------------------------------------------------
    @property
    def survey_zipcode(self):
        question_id = 2  # My zip code is
        answer_key = 'response'
        for d in self._get_bio_responses('openendedquestion', question_id):
            return d.get(answer_key, None)
        return None

    @property
    def survey_birthday(self):
        question_id = 1  # I was born on
        answer_key = 'response'
        birthdate = None
        try:
            for d in self._get_bio_responses('openendedquestion', question_id):
                if d.get(answer_key):
                    birthdate = datetime.strptime(d[answer_key], "%Y-%m-%d")
        except:
            pass
        return birthdate

    @property
    def age(self):
        bday = self.survey_birthday
        if bday:
            delta = datetime.today() - bday
            return int(delta.days / 365)
        return None

    @property
    def has_relationship(self):
        question_id = 3  # Relationships: I am currently...
        answer_key = 'selected_option_text'
        options = ['In a relationship', 'Married', 'Single and looking']
        for d in self._get_bio_responses('multiplechoicequestion', question_id):
            if d.get(answer_key) in options:
                return True
        return None

    @property
    def gender(self):
        """Returns the user's gender choice, converted to lowercase."""
        question_id = 1  # Gender: I am ...
        answer_key = 'selected_option_text'
        for d in self._get_bio_responses('multiplechoicequestion', question_id):
            if d.get(answer_key):
                return d[answer_key].lower().strip()
        return None

    @property
    def num_children(self):
        question_id = 6  # Children: I have...
        answer_key = 'selected_option_text'
        for d in self._get_bio_responses('multiplechoicequestion', question_id):
            return d.get(answer_key)
        return None

    # -------------------------------------------------------------------------
    # Initial Profile survey responses.
    # -------------------------------------------------------------------------
    @property
    def survey_employed(self):
        """Returns True or False. """
        question_id = 13  # I am currently employed.
        answer_key = 'selected_option'
        for d in self._get_profile_survey_responses('binaryquestion', question_id):
            return d.get(answer_key)
        return False

    @property
    def survey_in_relationship(self):
        """Returns True or False. """
        question_id = 14  # I am currently in a romantic relationship.
        answer_key = 'selected_option'
        for d in self._get_profile_survey_responses('binaryquestion', question_id):
            return d.get(answer_key)
        return False

    @property
    def survey_is_parent(self):
        """Returns True or False. """
        question_id = 16  # I am a parent.
        answer_key = 'selected_option'
        for d in self._get_profile_survey_responses('binaryquestion', question_id):
            return d.get(answer_key)
        return False

    @property
    def survey_has_degree(self):
        """Returns True or False. """
        question_id = 12  # I have a college degree.
        answer_key = 'selected_option'
        for d in self._get_profile_survey_responses('binaryquestion', question_id):
            return d.get(answer_key)
        return False

    @property
    def survey_sex(self):
        """Returns a string: 'Male' or 'Female' or None. """
        question_id = 8  # My sex is:
        answer_key = 'selected_option_text'
        qtype = 'multiplechoicequestion'
        result = None
        for d in self._get_profile_survey_responses(qtype, question_id):
            if d.get(answer_key):
                result = d.get(answer_key)
        if result is None:  # Fall back to gender
            result = self.gender
        return result

    def _get_survey_instrument_results(self, instrument_id):
        # UGH. We shoe-horned this shit into a survey and now there's no
        # clean way to get what *should* be a 1-to-1 relationship between
        # a user and some responses. I'm just hard-coding this for now because
        # i hate future me.
        results = []
        try:
            inst = Instrument.objects.get(pk=instrument_id)
            for qtype, question in inst.questions:
                data = {
                    'question_id': question.id,
                    'question_type': question.question_type,
                    'question_text': "{0}".format(question),
                    'response_url': question.get_api_response_url(),
                    'question_url': question.get_survey_question_url(),
                    'response_id': None,
                    'object_type': "surveyresult"
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
                    if question.question_type in ['binaryquestion', 'likertquestion']:
                        data['selected_option'] = r.selected_option
                        data['selected_option_text'] = r.selected_option_text
                    elif question.question_type == 'openendedquestion':
                        data['response'] = r.response
                    elif question.question_type == 'multiplechoicequestion':
                        data['selected_option'] = r.selected_option.id
                        data['selected_option_text'] = r.selected_option_text
                except ObjectDoesNotExist:
                    pass
                results.append(data)

        except Instrument.DoesNotExist:
            pass

        return results

    @property
    def profile_survey(self):
        return self._get_survey_instrument_results(6)

    @property
    def bio(self):
        return self._get_survey_instrument_results(4)

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
