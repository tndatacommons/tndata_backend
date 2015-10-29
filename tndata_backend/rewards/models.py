from django.contrib.postgres.fields import ArrayField
from django.db import models


class FunContent(models.Model):

    MESSAGE_TYPE_CHOICES = (
        ('quote', 'Quote'),
        ('fortune', 'Fortune'),
        ('fact', 'Fun Fact'),
        ('joke', 'Joke'),
    )

    message_type = models.CharField(
        max_length=32,
        choices=MESSAGE_TYPE_CHOICES,
        db_index=True,
    )
    message = models.TextField(
        blank=True,
        help_text="The main content. This could be the quote, joke, forture, etc"
    )
    author = models.CharField(
        max_length=256,
        blank=True,
        null=True,
        help_text="Author or attribution for a quote"
    )
    keywords = ArrayField(
        models.CharField(max_length=32, blank=True),
        default=list,
        blank=True,
    )

    def __str__(self):
        return self.message

    class Meta:
        ordering = ['id']
        verbose_name = "Fun Content"
        verbose_name_plural = "Fun Content"

    def _clean_keywords(self):
        """Split keywords on spaces, lowercase, and strip whitespace."""
        keywords = " ".join(self.keywords).lower()
        self.keywords = [kw.strip() for kw in keywords.split()]

    def save(self, *args, **kwargs):
        """This method ensurse we always perform a few tasks prior to saving:

        - Strip whitespace from message/author
        - Always clean keywords (strip & lowercase)

        """
        self.message = self.message.strip()
        self.author = self.author.strip()
        self._clean_keywords()
        super().save(*args, **kwargs)
