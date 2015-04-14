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


class URLMixin:
    """Contains methods for reversing Model URLs. This Mixin DRYs up the various
    get_XXXX_url methods that I use on models, particularly for Read, Update,
    and Delete actions.

    Models using this mixin can customize its behavior by specifying the
    following:

    * (required) urls_app_namespace: The url namespace used for the app
    * (required) urls_model_name: The model name used for the url
    * urls_slug_field: The unique slug used for the model. Default is `title_slug`
    * urls_icon_field: An icon field for the model. Defaut is None.
    * urls_image_field: An image field for the model. Defaut is None.

    And we make the assumption that we have the following URLs defined, e.g.
    for the Category model:

    * Read: category-detail
    * Update: category-update
    * Delete: category-delete

    """
    urls_app_namespace = None  # e.g. 'goals'
    urls_model_name = None  # e.g. 'category'
    urls_slug_field = "title_slug"  # e.g. 'name_slug', if different.
    urls_icon_field = None
    urls_image_field = None

    def _slug_field(self):
        return getattr(self, self.urls_slug_field, None)

    def _view(self, view_name):
        if self.urls_app_namespace is None or self.urls_model_name is None:
            raise ImproperlyConfigured(
                "Models using URLMixin must define both urls_app_namespace and "
                "urls_model_name."
            )
        return "{0}:{1}-{2}".format(
            self.urls_app_namespace, self.urls_model_name, view_name
        )

    def get_absolute_url(self):
        return reverse(self._view('detail'), args=[self._slug_field()])

    def get_update_url(self):
        return reverse(self._view('update'), args=[self._slug_field()])

    def get_delete_url(self):
        return reverse(self._view('delete'), args=[self._slug_field()])

    def get_absolute_icon(self):
        icon_field = getattr(self, self.urls_icon_field, None)
        if self.urls_icon_field and icon_field:
            return icon_field.url

    def get_absolute_image(self):
        image_field = getattr(self, self.urls_image_field, None)
        if self.urls_image_field and image_field:
            return image_field.url
