"""
This module contains Mixins.

"""
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
