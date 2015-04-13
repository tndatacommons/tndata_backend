"""
This module contains Mixins.

"""
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django_fsm import transition


class WorkflowMixin:
    """This mixin contains the transition methods used to switch states for
    Content; i.e. Categories, Goals, Behaviors, Actions.

    Once created, a piece of content can be in one of the following states:

    - Draft: Content is being created.
    - Pending Review: Content has been submitted for review and publish
    - Declined: Content is not suitbable for publishing and/or needs adjustment.
    - Published: Content is Available to the public via our api

    """
    # hack: needs to be defined here for transitions. Will get replaced by the
    # model's `state` field.
    state = None

    @transition(field=state, source="*", target='draft')
    def draft(self):
        pass

    @transition(field=state, source="draft", target='pending-review')
    def review(self):
        pass

    @transition(field=state, source="review", target='declined')
    def decline(self):
        pass

    @transition(field=state, source="review", target='published')
    def publish(self):
        pass


class RUDMixin:
    """Contains methods for reversing Read, Update, Delete URLs.

    To use this, the model must have a `title_slug` field, and it must define
    the following:

    * rud_app_namespace: The url namespace used for the app
    * rud_model_name: The model name used for the url

    And we make the assumption that we have the following URLs defined, e.g.
    for the Category model:

    * Read: category-detail
    * Update: category-update
    * Delete: category-delete

    """
    rud_app_namespace = None
    rud_model_name = None

    def _view(self, view_name):
        if self.rud_app_namespace is None or self.rud_model_name is None:
            raise ImproperlyConfigured(
                "Models using RUDMixin must define both rud_app_namespace and "
                "rud_model_name."
            )
        return "{0}:{1}-{2}".format(
            self.rud_app_namespace, self.rud_model_name, view_name
        )

    def get_absolute_url(self):
        return reverse(self._view('detail'), args=[self.title_slug])

    def get_update_url(self):
        return reverse(self._view('update'), args=[self.title_slug])

    def get_delete_url(self):
        return reverse(self._view('delete'), args=[self.title_slug])
