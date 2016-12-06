from datetime import timedelta
from random import sample
from string import ascii_uppercase, digits

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class OfficeHours(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    from_time = models.TimeField()
    to_time = models.TimeField()
    days = ArrayField(
        models.CharField(max_length=32, blank=True),
        default=list,
        blank=True,
    )
    expires_on = models.DateTimeField(blank=True, null=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        days = "".join([d[0] for d in self.days]).upper()
        return "{} - {} {}".format(self.from_time, self.to_time, days)

    class Meta:
        ordering = ['from_time', 'to_time']
        verbose_name = "Office Hours"
        verbose_name_plural = "Office Hours"

    def _set_expires(self):
        """Set an expiration time on the first save."""
        if self.expires_on is None:
            self.expires_on = timezone.now() + timedelta(days=30 * 5)

    def save(self, *args, **kwargs):
        self._set_expires()
        super().save(*args, **kwargs)


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
    name_slug = models.SlugField(max_length=256)

    start_time = models.TimeField()
    location = models.CharField(max_length=256)
    days = ArrayField(
        models.CharField(max_length=32, blank=True),
        default=list,
        blank=True,
    )
    code = models.CharField(max_length=4, unique=True)
    students = models.ManyToManyField(settings.AUTH_USER_MODEL)

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
        super().save(*args, **kwargs)

    def get_share_url(self):
        return reverse('officehours:share-course', args=[self.id])
