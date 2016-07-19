"""
This module defines data models relating to Organizations.

An Organization can be associated with:

    - content (Categories may include one or more organizations)
    - members (Users who are part of an organization, e.g. students)
    - staff (Users who work for an organization)
    - admins (Users who have some administrative access to an organization)

"""
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.text import slugify


class Organization(models.Model):
    name = models.CharField(
        max_length=512,
        unique=True,
        help_text="The organization's official name"
    )
    name_slug = models.SlugField(max_length=512, db_index=True, unique=True)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="member_organizations",
        help_text="Users who are members of this organization (e.g. students)"
    )
    staff = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="staff_organizations",
        help_text="Users who are staff this organization"
    )
    admins = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="admin_organizations",
        help_text="Users who are admins of this organization"
    )

    # TIMESTAMPS
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name', ]
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"

    def save(self, *args, **kwargs):
        """Always slugify the name prior to saving the model."""
        self.name_slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def categories(self):
        return self.category_set.all()

    def get_absolute_url(self):
        args = [self.pk, self.name_slug]
        return reverse('goals:organization-detail', args=args)

    def get_update_url(self):
        args = [self.pk, self.name_slug]
        return reverse('goals:organization-update', args=args)

    def get_delete_url(self):
        args = [self.pk, self.name_slug]
        return reverse('goals:organization-delete', args=args)
