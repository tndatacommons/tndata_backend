from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models

from . managers import QuestionManager
from . likert import LIKERT_SCALES


class Instrument(models.Model):
    title = models.CharField(max_length=128, unique=True, db_index=True)
    description = models.TextField(
        help_text="Optional Description for this Instrument"
    )
    user_instructions = models.TextField(
        blank=True,
        default='',
        help_text="A (very) short set of instructions for all questions within "
                  "this Instrument"
    )

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['title']
        verbose_name = "Instrument"
        verbose_name_plural = "Instruments"

    @property
    def questions(self):
        """Returns all questions associated with this Instrument. This is a
        list of tuples of the form [(Question Type, Question object) ... ]

        """
        results = [
            (q.__class__.__name__, q) for q in self.binaryquestion_set.all()
        ]
        results += [
            (q.__class__.__name__, q) for q in self.likertquestion_set.all()
        ]
        results += [
            (q.__class__.__name__, q) for q in self.openendedquestion_set.all()
        ]
        results += [
            (q.__class__.__name__, q) for q in self.multiplechoicequestion_set.all()
        ]
        return results

    def get_absolute_url(self):
        return reverse('survey:instrument-detail', args=[self.id])

    def get_update_url(self):
        return reverse('survey:instrument-update', args=[self.id])

    def get_delete_url(self):
        return reverse('survey:instrument-delete', args=[self.id])


class BaseQuestion(models.Model):
    """A Base class for a Question."""
    text = models.TextField(unique=True, help_text="The text of the question")
    order = models.IntegerField(default=0, help_text="Ordering of questions")
    available = models.BooleanField(default=True, help_text="Available to Users")
    priority = models.PositiveIntegerField(
        default=0,
        help_text="When specified, all questions with a priority of 1 will be "
                  "delivered to users before any questions of priority 2, and "
                  "so on..."
    )
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    instruments = models.ManyToManyField(
        Instrument,
        blank=True,
        null=True,
        help_text="The Instrument(s) to which this question belongs."
    )

    objects = QuestionManager()

    def __str__(self):
        return self.text

    class Meta:
        abstract = True
        ordering = ['order']


class BinaryQuestion(BaseQuestion):
    """A Question with a Yes/No Answer."""
    OPTIONS = (
        (False, "No"),
        (True, "Yes"),
    )

    class Meta:
        verbose_name = "Binary Question"
        verbose_name_plural = "Binary Questions"

    @property
    def options(self):
        return [{"id": o[0], "text": o[1]} for o in self.OPTIONS]

    def get_absolute_url(self):
        return reverse('survey:binary-detail', args=[self.id])

    def get_update_url(self):
        return reverse('survey:binary-update', args=[self.id])

    def get_delete_url(self):
        return reverse('survey:binary-delete', args=[self.id])

    @staticmethod
    def get_api_response_url():
        return reverse("binaryresponse-list")


class BinaryResponse(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    question = models.ForeignKey(BinaryQuestion)
    selected_option = models.BooleanField(default=False)
    submitted_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{}".format(self.selected_option_text)

    class Meta:
        verbose_name = "Binary Response"
        verbose_name_plural = "Binary Responses"

    @property
    def selected_option_text(self):
        return "Yes" if self.selected_option else "No"


class MultipleChoiceQuestion(BaseQuestion):
    """A Question that contains multiple choices for a response."""

    class Meta:
        verbose_name = "Multiple Choice Question"
        verbose_name_plural = "Multiple Choice Questions"

    @property
    def options(self):
        options = self.multiplechoiceresponseoption_set.filter(available=True)
        return list(options.values('id', 'text'))

    def get_absolute_url(self):
        return reverse('survey:multiplechoice-detail', args=[self.id])

    def get_update_url(self):
        return reverse('survey:multiplechoice-update', args=[self.id])

    def get_delete_url(self):
        return reverse('survey:multiplechoice-delete', args=[self.id])

    @staticmethod
    def get_api_response_url():
        return reverse("multiplechoiceresponse-list")


class MultipleChoiceResponseOption(models.Model):
    """A Response option for a `MultipleChoiceQuestion`."""

    question = models.ForeignKey(MultipleChoiceQuestion)
    text = models.TextField(help_text="The text of the response option")
    available = models.BooleanField(default=True, help_text="Available to Users")

    def __str__(self):
        return self.text

    class Meta:
        order_with_respect_to = "question"
        unique_together = ("question", "text")
        verbose_name = "Multiple Choice Response Option"
        verbose_name_plural = "Multiple Choice Response Options"


class MultipleChoiceResponse(models.Model):
    """A User's response to a Multiple Choice Question."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    question = models.ForeignKey(MultipleChoiceQuestion)
    selected_option = models.ForeignKey(MultipleChoiceResponseOption)
    submitted_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{}".format(self.selected_option)

    class Meta:
        verbose_name = "Multiple Choice Response"
        verbose_name_plural = "Multiple Choice Responses"

    @property
    def selected_option_text(self):
        return self.selected_option.text


class OpenEndedQuestion(BaseQuestion):
    """An Open-Ended Question Allows for a plain-text response."""

    class Meta:
        verbose_name = "Open-Ended Question"
        verbose_name_plural = "Open-Ended Questions"

    def get_absolute_url(self):
        return reverse('survey:openended-detail', args=[self.id])

    def get_update_url(self):
        return reverse('survey:openended-update', args=[self.id])

    def get_delete_url(self):
        return reverse('survey:openended-delete', args=[self.id])

    @staticmethod
    def get_api_response_url():
        return reverse("openendedresponse-list")


class OpenEndedResponse(models.Model):
    """A User's response to an `OpenEndedQuestion`."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    question = models.ForeignKey(OpenEndedQuestion)
    response = models.TextField()
    submitted_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{}".format(self.response)

    class Meta:
        verbose_name = "Open-Ended Response"
        verbose_name_plural = "Open-Ended Responses"


class LikertQuestion(BaseQuestion):
    """A seven-level likert item/question
    http://en.wikipedia.org/wiki/Likert_scale#Likert_scales_and_items

    """
    SCALE_CHOICES = [
        (k, " ".join(k.split("_")).title()) for k in LIKERT_SCALES.keys()
    ]
    scale = models.CharField(
        max_length=32,
        default="5_point_agreement",  # See likert.LIKERT_SCALES
        choices=SCALE_CHOICES,
        help_text="Select the Scale for this question"
    )

    class Meta:
        verbose_name = "Likert Question"
        verbose_name_plural = "Likert Questions"

    @property
    def scale_text(self):
        return " ".join(self.scale.split("_")).title()

    @property
    def choices(self):
        return LIKERT_SCALES[self.scale]

    @property
    def options(self):
        """Kind of a hack, but this follows a similar pattern as in the
        MultipleChoiceQuestion model. Returns the possible options for a
        question."""
        return [{'id': o[0], 'text': o[1]} for o in self.choices]

    def get_absolute_url(self):
        return reverse('survey:likert-detail', args=[self.id])

    def get_update_url(self):
        return reverse('survey:likert-update', args=[self.id])

    def get_delete_url(self):
        return reverse('survey:likert-delete', args=[self.id])

    @staticmethod
    def get_api_response_url():
        return reverse("likertresponse-list")


class LikertResponse(models.Model):
    """Response to a `LikertQuestion`.
    http://en.wikipedia.org/wiki/Likert_scale#Likert_scales_and_items

    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    question = models.ForeignKey(LikertQuestion)
    # TODO: I'd like to enforce choices on selected_option, but those would
    # have to be set dynamically based on the question's scale.
    selected_option = models.PositiveIntegerField()
    submitted_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{}".format(self.get_selected_option_display())

    class Meta:
        verbose_name = "Likert Response"
        verbose_name_plural = "Likert Responses"

    @property
    def selected_option_text(self):
        return self.get_selected_option_display()

    def get_selected_option_display(self):
        for value, text in self.question.choices:
            if self.selected_option == value:
                return text
