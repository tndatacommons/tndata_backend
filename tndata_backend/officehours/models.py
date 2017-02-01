from datetime import timedelta
from random import sample
from string import ascii_uppercase, digits

from django.conf import settings
from django.contrib.postgres.fields import ArrayField, JSONField
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from .managers import ExpiresOnManager


# Shortcut dict for displaying single-char representations.
DAYS = {
    'Sunday': 'S',
    'Monday': 'M',
    'Tuesday': 'T',
    'Wednesday': 'W',
    'Thursday': 'R',
    'Friday': 'F',
    'Saturday': 'Z',
}

# Dict for sorting lists of days.
DAYS_SORT = {
    'Sunday': 0,
    'Monday': 1,
    'Tuesday': 2,
    'Wednesday': 3,
    'Thursday': 4,
    'Friday': 5,
    'Saturday': 6,
}


class OfficeHours(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    # The OfficeHours schedule; We want data that looks like this
    # {
    #   'DAY': [[from_time, to_time], ... ],
    #   ...
    #   'Friday': [["15:30", "16:30], ["14:30", "15:00"], ]
    # }
    schedule = JSONField(default={}, blank=True)
    expires_on = models.DateTimeField(blank=True, null=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Officehours #{}".format(self.id)

    class Meta:
        ordering = ['created_on', ]
        verbose_name = "Office Hours"
        verbose_name_plural = "Office Hours"

    def _set_expires(self):
        """Set an expiration time on the first save."""
        if self.expires_on is None:
            self.expires_on = timezone.now() + timedelta(days=30 * 5)

    def save(self, *args, **kwargs):
        self._set_expires()
        super().save(*args, **kwargs)

    @property
    def days(self):
        """Return a list of days on which there are office hours"""
        days = list(self.schedule.keys())
        days.sort(key=DAYS_SORT.get)
        return days

    def get_schedule(self):
        """Returns a sorted list of meeting days / times that should be
        iterable in templates (for displaying). e.g.

            for day, times in obj.get_schedule  ...

        The format is:

            [(day, [[from-time, to-time], ...]),  ... ]

        """
        schedule = list(self.schedule.items())
        schedule.sort(key=lambda tup: DAYS_SORT.get(tup[0]))
        return schedule

    def get_absolute_url(self):
        return reverse('officehours:officehours-details', args=[self.id])

    def get_delete_url(self):
        return reverse('officehours:delete-officehours', args=[self.id])

    objects = ExpiresOnManager()


def generate_course_code(length=4):
    """Generate a 4-character code consistign of Uppercase letters + digits,
    and ensure that it's not already associated with a Course.

    Returns a string.

    """
    code = "".join(sample(ascii_uppercase + digits, length))
    while Course.objects.filter(code=code).exists():
        code = "".join(sample(ascii_uppercase + digits, length))
    return code


class Course(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="teaching",
        help_text="The Teacher"
    )
    name = models.CharField(max_length=256)
    name_slug = models.SlugField(max_length=256, blank=True)

    start_time = models.TimeField()
    location = models.CharField(max_length=256)
    days = ArrayField(
        models.CharField(max_length=32, blank=True),
        default=list,
        blank=True,
    )
    code = models.CharField(max_length=4, unique=True, blank=True)
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)

    expires_on = models.DateTimeField(blank=True, null=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['start_time', 'name']
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    def display_time(self):
        return "{} {}".format(
            self.start_time.strftime("%I:%M%p"),
            "".join(d[0] for d in self.days).upper()
        )

    def _set_code(self):
        if not self.code:
            self.code = generate_course_code()

    def _set_name_slug(self):
        self.name_slug = slugify(self.name)

    def _set_expires(self):
        """Set an expiration time on the first save."""
        if self.expires_on is None:
            self.expires_on = timezone.now() + timedelta(days=30 * 5)

    def save(self, *args, **kwargs):
        self._set_expires()
        self._set_name_slug()
        self._set_code()
        # Ensure our list of days is always ordered correctly
        self.days.sort(key=DAYS_SORT.get)
        super().save(*args, **kwargs)

    @property
    def meetingtime(self):
        """Return a condensed string format for the days and times."""
        days = [DAYS[d] for d in sorted(self.days, key=DAYS_SORT.get)]
        return "{} {}".format(
            "".join(days),
            self.start_time.strftime("%H:%M"),
        )

    def get_absolute_url(self):
        return reverse('officehours:course-details', args=[self.id])

    def get_share_url(self):
        return reverse('officehours:share-course', args=[self.id])

    def get_delete_url(self):
        return reverse('officehours:delete-course', args=[self.id])

    def get_officehours(self):
        """Return the instructor's current office hours."""
        return OfficeHours.objects.current().filter(user=self.user)

    objects = ExpiresOnManager()
