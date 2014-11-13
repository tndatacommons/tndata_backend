from django.conf import settings
from django.db import models


class BaseQuestion(models.Model):
    """A Base class for a Question."""
    text = models.TextField(unique=True, help_text="The text of the question")
    order = models.IntegerField(default=0, help_text="Ordering of questions")
    available = models.BooleanField(default=True, help_text="Available to Users")

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


class OpenEndedQuestion(BaseQuestion):
    """An Open-Ended Question Allows for a plain-text response."""

    class Meta:
        verbose_name = "Open-Ended Question"
        verbose_name_plural = "Open-Ended Questions"


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


class Goal(models.Model):
    CATEGORIES = (
        ('lifegoal', 'Life Goal'),
    )
    category = models.CharField(max_length=32, choices=CATEGORIES)
    text = models.TextField(unique=True, help_text="The text of a User-Goal")
    description = models.TextField(blank=True, help_text="Optional Description")
    order = models.IntegerField(default=0, help_text="Ordering of questions")

    def __str__(self):
        return "{}: {}".format(self.category, self.text)

    class Meta:
        ordering = ["order"]
        verbose_name = "Goal"
        verbose_name_plural = "Goals"


class LikertQuestion(BaseQuestion):
    """A five-level likert item/question
    http://en.wikipedia.org/wiki/Likert_scale#Likert_scales_and_items

    """
    goal = models.ManyToManyField(
        Goal,
        null=True,
        help_text="Attach this question to one or more Goals"
    )

    class Meta:
        verbose_name = "Likert Question"
        verbose_name_plural = "Likert Questions"


class LikertResponse(models.Model):
    """Response to a `LikertQuestion`.
    http://en.wikipedia.org/wiki/Likert_scale#Likert_scales_and_items

    """
    STRONGLY_DISAGREE = 1
    DISAGREE = 2
    NEITHER = 3
    AGREE = 4
    STRONGLY_AGREE = 5

    LIKERT_CHOICES = (
        (STRONGLY_DISAGREE, 'Strongly Disagree'),
        (DISAGREE, 'Disagree'),
        (NEITHER, 'Neither Agree nor Disagree'),
        (AGREE, 'Agree'),
        (STRONGLY_AGREE, 'Strongly Agree'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    goal = models.ForeignKey(Goal)
    question = models.ForeignKey(LikertQuestion)
    selected_option = models.PositiveIntegerField(choices=LIKERT_CHOICES)
    submitted_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{}".format(self.selected_option)

    class Meta:
        verbose_name = "Likert Response"
        verbose_name_plural = "Likert Responses"
