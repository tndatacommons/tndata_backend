from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models


# TODO: How to associate a question with a Channel in the app (Category?)
# TODO: How to serve questions to the app in the simplest manner.


class QuestionManager(models.Manager):

    def available(self, *args, **kwargs):
        qs = self.get_queryset()
        return qs.filter(available=True)


class BaseQuestion(models.Model):
    """A Base class for a Question."""
    text = models.TextField(unique=True, help_text="The text of the question")
    order = models.IntegerField(default=0, help_text="Ordering of questions")
    available = models.BooleanField(default=True, help_text="Available to Users")
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    objects = QuestionManager()

    def __str__(self):
        return self.text

    class Meta:
        abstract = True
        ordering = ['order']


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
    STRONGLY_DISAGREE = 1
    DISAGREE = 2
    SLIGHTLY_DISAGREE = 3
    NEITHER = 4
    SLIGHTLY_AGREE = 5
    AGREE = 6
    STRONGLY_AGREE = 7

    LIKERT_CHOICES = (
        (STRONGLY_DISAGREE, 'Strongly Disagree'),
        (DISAGREE, 'Disagree'),
        (SLIGHTLY_DISAGREE, 'Slightly Disagree'),
        (NEITHER, 'Neither Agree nor Disagree'),
        (SLIGHTLY_AGREE, 'Slightly Agree'),
        (AGREE, 'Agree'),
        (STRONGLY_AGREE, 'Strongly Agree'),
    )

    class Meta:
        verbose_name = "Likert Question"
        verbose_name_plural = "Likert Questions"

    @property
    def options(self):
        """Kind of a hack, but this follows a similar pattern as in the
        MultipleChoiceQuestion model. Returns the possible options for a
        question."""
        return [{'id': o[0], 'text': o[1]} for o in self.LIKERT_CHOICES]

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
    selected_option = models.PositiveIntegerField(
        choices=LikertQuestion.LIKERT_CHOICES
    )
    submitted_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{}".format(self.get_selected_option_display())

    class Meta:
        verbose_name = "Likert Response"
        verbose_name_plural = "Likert Responses"

    @property
    def selected_option_text(self):
        return self.get_selected_option_display()
