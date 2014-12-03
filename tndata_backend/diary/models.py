from django.conf import settings
from django.db import models


class Entry(models.Model):
    """An Entry in the Diary"""

    GREAT = 5
    WELL = 4
    FINE = 3
    BAD = 2
    AWFUL = 1

    FEELING_CHOICES = (
        (GREAT, 'Great'),
        (WELL, 'Well'),
        (FINE, 'Just Fine'),
        (BAD, 'Bad'),
        (AWFUL, 'Awful'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    rank = models.PositiveIntegerField(choices=FEELING_CHOICES, db_index=True)
    notes = models.TextField(
        blank=True,
        help_text="Notes on why you are feeling this way."
    )
    submitted_on = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return self.get_rank_display()

    class Meta:
        ordering = ['submitted_on']
        verbose_name = "Entry"
        verbose_name_plural = "Entries"

    @property
    def rank_display(self):
        return self.get_rank_display()
