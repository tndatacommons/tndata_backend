"""
Models for Packages.

"""
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models

from .public import Action, Behavior, Category, Goal
from .users import UserAction, UserBehavior, UserCategory, UserGoal
from ..managers import PackageEnrollmentManager


class PackageEnrollment(models.Model):
    """A mapping of users who've been enrolled in various *Packaged Content*
    e.g. Categories. This model tracks when they were enrolled, which categories
    they were enrolled in, and who enrolled them.

    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    category = models.ForeignKey(Category)
    goals = models.ManyToManyField(Goal)
    prevent_custom_triggers = models.BooleanField(
        default=False,
        help_text="Setting this option will prevent users from overriding the "
                  "default reminder times for actions within the selected goals."
    )
    accepted = models.BooleanField(default=False)
    enrolled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='enrolled'
    )
    updated_on = models.DateTimeField(auto_now=True)
    enrolled_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['enrolled_on']
        verbose_name = "Package Enrollment"
        verbose_name_plural = "Package Enrollments"

    def __str__(self):
        return "{0} enrolled on {1}".format(
            self.user.get_full_name(),
            self.enrolled_on
        )

    @property
    def rendered_consent_summary(self):
        return self.category.rendered_consent_summary

    @property
    def rendered_consent_more(self):
        return self.category.rendered_consent_more

    def get_absolute_url(self):
        """Currently, this is the PackageDetailView, which provides a list of
        enrollments."""
        return reverse("goals:package-detail", args=[self.pk])

    def get_accept_url(self):
        return reverse("goals:accept-enrollment", args=[self.pk])

    def accept(self):
        self.accepted = True
        self.save()
        self.create_user_mappings()

    def create_user_mappings(self):
        """Creates all of the User-mappings for the associated categories and
        all child content."""
        # This is terribly inefficient, because we'll likely be doing
        # this for a number of users at once.
        UserCategory.objects.get_or_create(user=self.user, category=self.category)

        # Enroll the user in the Goals
        goals = self.goals.all()
        for goal in goals:
            ug = UserGoal.objects.get_or_create(user=self.user, goal=goal)
            ug.primary_category = self.category
            ug.save()

        # Enroll the User in the Behaviors
        behaviors = Behavior.objects.published().filter(goals=goals).distinct()
        for behavior in behaviors:
            UserBehavior.objects.get_or_create(user=self.user, behavior=behavior)

        # Enroll the User in the Actions
        actions = Action.objects.published().filter(behavior__in=behaviors)
        actions = actions.distinct()
        for action in actions:
            ua = UserAction.objects.get_or_create(user=self.user, action=action)
            ua.primary_category = self.category
            ua.primary_goal = ua.get_primary_goal()
            ua.save()

    objects = PackageEnrollmentManager()
