"""

"""
import logging

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.text import slugify

logger = logging.getLogger(__file__)


class Question(models.Model):
    """

    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    title = models.CharField(
        max_length=256,
        db_index=True,
        help_text="A question posed to the community."
    )
    title_slug = models.SlugField(max_length=256, blank=True)
    content = models.TextField(
        blank=True,
        help_text="Additional details or description to support your question."
    )
    published = models.BooleanField(default=False)
    votes = models.IntegerField(default=0, blank=True)
    voters = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="upvoted_questions",
        help_text="The group of users that have up-voted this question."
    )
    keywords = ArrayField(
        models.CharField(max_length=32, blank=True),
        default=list,
        blank=True,
        help_text="Keywords for this question, comma-separated."
    )

    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['votes', 'created_on', 'title']
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        get_latest_by = 'created_on'

    def save(self, *args, **kwargs):
        self.title_slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        # /questions/<question_pk>/<title_slug>/
        args = [self.pk, self.title_slug]
        return reverse("questions:question-details", args=args)

    def get_answer_question_url(self):
        args = [self.pk, self.title_slug]
        return reverse("questions:post-answer", args=args)

    def get_upvote_url(self):
        args = [self.pk, self.title_slug]
        return reverse("questions:upvote-question", args=args)


class Answer(models.Model):
    question = models.ForeignKey(Question)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    content = models.TextField(
        help_text="Your answer to a question."
    )
    voters = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="upvoted_answers",
        help_text="The group of users that have up-voted this answer."
    )
    votes = models.IntegerField(default=0, blank=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{}...".format(self.content[:20])

    class Meta:
        ordering = ['votes', 'created_on', 'content']
        verbose_name = "Answer"
        verbose_name_plural = "Answers"
        get_latest_by = 'created_on'

    @property
    def teaser(self):
        return self.__str__()

    def get_absolute_url(self):
        # /questions/<question_pk>/<title_slug>/#answer-<answer_pk>
        args = [self.question.pk, self.question.title_slug]
        url = reverse("questions:question-details", args=args)
        return "{}#answer-{}".format(url, self.pk)

    def get_upvote_url(self):
        args = [self.question.pk, self.question.title_slug, self.pk]
        return reverse("questions:upvote-answer", args=args)
