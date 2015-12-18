from datetime import timedelta
from django.db.models import Avg, Q
from django.utils import timezone
from drf_haystack.viewsets import HaystackViewSet
from drf_haystack.filters import HaystackHighlightFilter
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.authentication import (
    SessionAuthentication, TokenAuthentication
)
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from redis_metrics import metric
from utils.user_utils import local_day_range

from . import models
from . import serializers
from . import settings
from . mixins import DeleteMultipleMixin


class IsOwner(permissions.BasePermission):
    """Only allow owners of an object to view/edit it."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Categories are containers for similar Goals. A Goal may appear in more
    than one category.

    Each Category has at least the following bits of information:

    * id: The unique database identifier for the category
    * order: Controls the order in which Categories are displayed.
    * title: The unique Title (or name) of the Category
    * title_slug: A url-friendly version of the title.
    * description: A short description of this Category. Plain text (possibly markdown)
    * html_description: HTML version of the description.
    * icon_url: A URL for a square image. This is the category's Icon.
    * image_url: A URL for a larger image associated with the category. Use as the
      category's _hero_ image above each tab.
    * color: A primary color for content in this category
    * secondary_color: A secondary color for content
    * packaged_content: True or False. Is this category a package.
    * goals: A list of goals that appear in this category. See the [Goals](/api/goals/)
        endpoint for more information.

    ## Category Endpoints

    Each category is available at an endpoint based on it's database ID: `/api/categories/{id}/`.

    ----

    """
    queryset = models.Category.objects.published()
    serializer_class = serializers.CategorySerializer


class GoalViewSet(viewsets.ReadOnlyModelViewSet):
    """Goals contain the following information:

    * id: The unique database identifier for the goal
    * title: A unique Title (or name) for the goal.
    * title_slug: A url-friendly version of the title.
    * description: A short description for the goal. Plain text (possibly markdown)
    * html_description: HTML version of the description.
    * outcome: Additional (optional) text that may describe an expected outcome
      of pursing this Goal.
    * icon_url: A URL for an image associated with the category
    * categories: A list of [Categories](/api/categories/) in which the goal appears.

    ## Goal Endpoints

    Each goal is available at an endpoint based on it's database ID: `/api/goals/{id}/`.

    ## Filtering

    Goals can be filtered using a querystring paramter. Currently, filtering is
    only availble for categories; i.e. You can retrieve goals for a category
    by providing a category id: `/api/goals/?category={category_id}`

    ----

    """
    queryset = models.Goal.objects.published()
    serializer_class = serializers.GoalSerializer

    def get_queryset(self):
        if 'category' in self.request.GET:
            self.queryset = self.queryset.filter(
                categories__id=self.request.GET['category']
            )
        return self.queryset


class TriggerViewSet(viewsets.ReadOnlyModelViewSet):
    """A Trigger represents information we send to a user (via a push
    notification) to remind them to take an action or think about a behavior.

    **NOTE**: This is still a work in progress and subject to change; This
    endpoint currently only displayes the set of _default_ triggers; i.e. those
    that don't belong to a particular user.

    Triggers contain the following:

    * id: The unique database identifier for the trigger
    * user: User to which the trigger belongs (will be `null` for this endpoint)
    * name: A unique name for a trigger.
    * name_slug: A web-friendly version of the name.
    * time: for "time" trigger types, the time at which an alert is sent.
    * recurrences: For "time" triggers, this is an iCalendar (rfc2445) format.
      This field is optional and may be null.
    * recurrences_display: human-readible information for `recurrences`
    * next: Date/Time for the next occurance of this trigger

    ## Trigger Endpoints

    Each trigger is available at an endpoint based on it's database ID: `/api/triggers/{id}/`.

    ----

    """
    queryset = models.Trigger.objects.default()
    serializer_class = serializers.TriggerSerializer


class BehaviorViewSet(viewsets.ReadOnlyModelViewSet):
    """A Behavior Sequence (aka a *Behavior*) is an abstract
    behavior as well as a potential container for concrete actions.

    Each Behavior object contains the following:

    * id: The unique database identifier for the behavior
    * title: A unique, Formal title. Use this to refer to this item.
    * title_slug: A url-friendly version of title.
    * description: A short description of the Behavior. Plain text (possibly markdown)
    * html_description: HTML version of the description.
    * more_info: Additional information displayed when the user drills down
      into the content. Contains markdown.
    * html_more_info: HTML version of the `more_info` field.
    * external_resource = A link or reference to an outside resource necessary for adoption
    * external_resource_name = A human-friendly name for the external resource
    * default_trigger: A trigger/reminder for this behavior. See the
        [Trigger](/api/triggers/) endpoint for more details. The time included
        in this trigger contains no timezone information, so it's safe to assume
        it's always in the user's local time.
    * notification_text: Text of the message delivered through notifications
    * icon_url: A URL for an icon associated with the category
    * image_url: (optional) Possibly larger image for this item.
    * goals: A list of goals in which this Behavior appears.

    ## Behavior Endpoints

    Each item is available at an endpoint based on it's database ID: `/api/behaviors/{id}/`.

    ## Filtering

    Behaviors can be filtered using a querystring parameter. Currently,
    filtering is availble for both goals and categories. You can filter by an
    ID or a slug.

    * Retrieve all *Behavior*s that belong to a particular goal:
      `/api/behaviors/?goal={goal_id}` or by slug
      `/api/behaviors/?goal={goal_title_slug}`
    * Retrieve all *Behavior*s that belong to a particular category:
      `/api/behaviors/?category={category_id}` or by slug:
      `/api/behaviors/?category={category_title_slug}`

    ----

    """
    queryset = models.Behavior.objects.published()
    serializer_class = serializers.BehaviorSerializer

    def get_queryset(self):
        category = self.request.GET.get('category', None)
        goal = self.request.GET.get('goal', None)

        if category is not None and category.isnumeric():
            # Filter by Category.id
            self.queryset = self.queryset.filter(goals__categories__id=category)
        elif category is not None:
            # Filter by Category.title_slug
            self.queryset = self.queryset.filter(goals__categories__title_slug=category)

        if goal is not None and goal.isnumeric():
            # Filter by Goal.id
            self.queryset = self.queryset.filter(goals__id=goal)
        elif goal is not None:
            # Filter by Goal.title_slug
            self.queryset = self.queryset.filter(goals__title_slug=goal)

        return self.queryset


class ActionViewSet(viewsets.ReadOnlyModelViewSet):
    """A Behavior Action (aka an *Action*) is a concrete action that an person
    can perform.

    Each Action object contains the following:

    * id: The unique database identifier for the action
    * behavior: The [Behavior](/api/behaviors/) to which the action belongs
    * sequence_order: The order in which actions should be displayed/performed (if any)
    * title: A unique, Formal title. Use this to refer to this item.
    * title_slug: A url-friendly version of title.
    * description: A short description of the Action. Plain text (possibly markdown)
    * html_description: HTML version of the description.
    * more_info: Additional information displayed when the user drills down
      into the content. Contains markdown.
    * html_more_info: HTML version of the `more_info` field.
    * external_resource = A link or reference to an outside resource necessary for adoption
    * external_resource_name = A human-friendly name for the external resource
    * default_trigger: A trigger/reminder for this action. See the
        [Trigger](/api/triggers/) endpoint for more details. The time included
        in this trigger contains no timezone information, so it's safe to assume
        it's always in the user's local time.
    * notification_text: Text of the message delivered through notifications
    * icon_url: A URL for an icon associated with the category
    * image_url: (optional) Possibly larger image for this item.

    ## Action Endpoints

    Each item is available at an endpoint based on it's database ID: `/api/actions/{id}/`.

    ## Filtering

    Actions can be filtered using a querystring parameter. Currently,
    filtering is availble for goals, categories, and behaviors. You can filter
    by an ID or a slug.

    * Retrieve all *Actions*s that belong to a particular Behavior:
      `/api/actions/?behavior={behavior_id}`, or by slug:
      `/api/actions/?behavior={behavior_title_slug}`
    * Retrieve all *Action*s that belong to a particular goal:
      `/api/actions/?goal={goal_id}`, or by slug:
      `/api/actions/?goal={goal_title_slug}`
    * Retrieve all *Action*s that belong to a particular category:
      `/api/actions/?category={category_id}`, or by slug:
      `/api/actions/?category={category_title_slug}`

    ----

    """
    queryset = models.Action.objects.published()
    serializer_class = serializers.ActionSerializer

    def get_queryset(self):
        category = self.request.GET.get("category", None)
        goal = self.request.GET.get("goal", None)
        behavior = self.request.GET.get("behavior", None)
        if behavior is None and 'sequence' in self.request.GET:
            behavior = self.request.GET.get("sequence", None)

        if category is not None and category.isnumeric():
            # Filter by Category.id
            self.queryset = self.queryset.filter(
                behavior__goals__categories__id=category
            )
        elif category is not None:
            # Filter by Category.title_slug
            self.queryset = self.queryset.filter(
                behavior__goals__categories__title_slug=category
            )

        if goal is not None and goal.isnumeric():
            # Filter by Goal.id
            self.queryset = self.queryset.filter(behavior__goals__id=goal)
        elif goal is not None:
            # Filter by Goal.title_slug
            self.queryset = self.queryset.filter(behavior__goals__title_slug=goal)

        if behavior is not None and behavior.isnumeric():
            self.queryset = self.queryset.filter(behavior__pk=behavior)
        elif behavior is not None:
            self.queryset = self.queryset.filter(behavior__title_slug=behavior)

        return self.queryset


class UserGoalViewSet(mixins.CreateModelMixin,
                      mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.DestroyModelMixin,
                      DeleteMultipleMixin,
                      viewsets.GenericViewSet):
    """This endpoint represents a mapping between [Users](/api/users/) and
    [Goals](/api/goals/).

    GET requests to this page will simply list this mapping for the authenticated
    user.

    ## Fields

    This endpoint returns resources with the following fields.

    * `id`: A unique identifier for the `UserGoal` mapping.
    * `user`: A unique identifier for the `User`
    * `goal`: An object that represents the `Goal` selected by the user
    * `user_categories`: An array of `Category` objects selected by the user,
      that are also parents of this goal.
    * `primary_category`: The primary category for this goal, based on the
      user's selection.
    * `user_behaviors_count`: the number of child Behaviors that the user has
      selected that are contained in this goal.
    * `user_behaviors`: An array of `Behavior` objects selected by the user.
    * `created_on`: Time at which the user selected this item.
    * `progress_value`: The user's self-reported progress toward *Behaviors* in
      this goal.
    * `goal_progress`: An object containing information on the user's progress
      toward the completion of their scheduled actions within this goal. It
      contains the following information:

        - `id`: a unique id for the GoalProgress instance.
        - `goal`: the goal's unique id
        - `usergoal`: The unique id of the parent UserGoal
        - `current_score`: The aggregate Behavior-rerporting score.
        - `current_total`: The sum of user-reported behavior progresses within
          this goal.
        - `max_total`: The maximum possible value for the Behavior-reported score.
        - `daily_actions_total`: Number of actions scheduled for _this day_.
        - `daily_actions_completed`: Number of actions the user completed in
          _this day_
        - `daily_action_progress`: Daily progress percentage (as a float). This
          is calculated with `daily_actions_completed` / `daily_actions_total`
        - `daily_action_progress_percent`: The daily progress expressed as an
          integer percentage.
        - `weekly_actions_total`: Number of actions scheduled for the past 7 days
        - `weekly_actions_completed`: Number of actions completed over the past
          7 days
        - `weekly_action_progress`: Percentage of completed actions for the week.
        - `weekly_action_progress_percent`: The weekly progress expressed as an
          integer percentage.
        - `actions_total`:  Number of actions scheduled for our historical
          reporting period
        - `actions_completed`: Number of actions completed during our historical
          reporting period.
        - `action_progress`:  Percentage of actions completed (as a float) during
          the historical reporting period.
        - `action_progress_percent`: The progress expressed as an integer
          percentage.
        - `reported_on`: Date/Time on which this data was recorded.

    * `custom_triggers_allowed`: A boolean that indicates whether or not a user
      should be able to customize the reminders beneath this content

    ## Adding a Goal

    To associate a Goal with a User, POST to `/api/users/goals/` with the
    following data:

        {'goal': GOAL_ID}

    ## Adding multiple Goals in one request

    This endpoint also allows you to associate multiple goals with a user
    in a single request. To do this, POST an array of goal IDs, e.g.:

        [
            {'goal': 3},
            {'goal': 4},
            {'goal': 5}
        ]

    ## Removing multiple Goals in one request.

    This endpoint also allows you to remove  multiple instances of the
    user-to-goal association. Tod do this, send a DELETE request with
    an array of `usergoal` IDs, e.g.:

        [
            {'usergoal': 3},
            {'usergoal': 4},
            {'usergoal': 5}
        ]

    ## Viewing the Goal data

    Additional information for the Goal mapping is available at
    `/api/users/goals/{usergoal_id}/`. In this case, `{usergoal_id}` is the
    database id for the mapping between a user and a goal.

    ## Removing a Goal from the user's list.

    Send a DELETE request to the usergoal mapping endpoint:
    `/api/users/goals/{usergoal_id}/`.

    ## Update a Goal Mapping.

    Updating a goal mapping is currently not supported.

    ## Additional information

    The Goals that a User has selected are also available through the
    `/api/users/` endpoint as a `goals` object on the user.

    Each results object also includes a `user_categories` object in addition to
    a `goal` object. The `user_categories` object is a list of Categories in
    which the goal belongs that have also been selected by the User. Related:
    [/api/users/categories/](/api/users/categories/).

    ----

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.UserGoal.objects.published()
    serializer_class = serializers.UserGoalSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return models.UserGoal.objects.accepted_or_public(user=self.request.user)

    def get_serializer(self, *args, **kwargs):
        """Ensure we pass `many=True` into the serializer if we're dealing
        with a list of items."""
        if isinstance(self.request.data, list):
            kwargs['many'] = True
        return super(UserGoalViewSet, self).get_serializer(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Only create objects for the authenticated user."""
        if isinstance(request.data, list):
            # We're creating multiple items.
            for d in request.data:
                d['user'] = request.user.id
        else:
            # We're creating a single items.
            request.data['user'] = request.user.id
        return super(UserGoalViewSet, self).create(request, *args, **kwargs)


class UserBehaviorViewSet(mixins.CreateModelMixin,
                          mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.DestroyModelMixin,
                          mixins.UpdateModelMixin,
                          DeleteMultipleMixin,
                          viewsets.GenericViewSet):
    """This endpoint represents a mapping between [Users](/api/users/) and
    [Behaviors](/api/behaviors/).

    GET requests to this page will simply list this mapping for the authenticated
    user.

    ## Fields

    This endpoint returns resources with the following fields.

    * `id`: A unique identifier for the `UserBehavior` mapping.
    * `user`: A unique identifier for the `User`
    * `behavior`: An object that represents the `Behavior` selected by the user
    * `behavior_progress`: An object containing information on the user's
      progress toward the completion of their scheduled actions within this
      behavior. It contains the following information:

        - `id`: a unique id for the GoalProgress instance.
        - `user`: the user's unique id
        - `user_behavior`: The unique id of the parent UserBehavior
        - `status`: An integer representing the user's daily reported progress,
          (1 means Off Course, 2 is Seeking, 3 is On Course).
        - `status_display`: A human-readable version of status.
        - `daily_actions_total`: Number of actions scheduled for _this day_.
        - `daily_actions_completed`: Number of actions the user completed in
          _this day_
        - `daily_action_progress`: Daily progress percentage (as a float). This
          is calculated with `daily_actions_completed` / `daily_actions_total`
        - `reported_on`: Date/Time on which this data was recorded.
        - `object_type`: Will always be `behaviorprogress`

    * `custom_trigger`: (will be `null`). This is currently not implemented.
    * `custom_triggers_allowed`: A boolean that indicates whether or not a user
      should be able to customize the reminders beneath this content
    * `user_categories`: An array of `Category` objects that have been selected
      by the user, and that are also parents of this behavior (through Goals)
    * `user_goals`: An array of `Goal` objects that have been selected by the
      user, and that are also parents of this behavior.
    * `user_actions_count`: the number of child Actions that the user has
      selected that are contained in this behavior.
    * `user_actions`: An array of `Action` objects selected by the user.
    * `created_on`: Time at which the user selected this item.

    ## Adding a Behavior

    To associate a Behavior with a User, POST to `/api/users/behaviors/` with the
    following data:

        {'behavior': BEHAVIOR_ID}

    ## Adding multiple Behaviors in one request

    This endpoint also allows you to associate multiple behaviors with a user
    in a single request. To do this, POST an array of behavior IDs, e.g.:

        [
            {'behavior': 3},
            {'behavior': 4},
            {'behavior': 5}
        ]

    ## Removing multiple Behaviors in one request.

    This endpoint also allows you to remove  multiple instances of the
    user-to-behavior association. Tod do this, send a DELETE request with
    an array of `userbehavior` IDs, e.g.:

        [
            {'userbehavior': 3},
            {'userbehavior': 4},
            {'userbehavior': 5}
        ]

    ## Viewing the Behavior data

    Additional information for the Behavior mapping is available at
    `/api/users/behaviors/{userbehavior_id}/`. In this case, `{userbehavior_id}`
    is the database id for the mapping between a user and a behavior.

    ## Removing a Behavior from the user's list.

    Send a DELETE request to the userbehavior mapping endpoint:
    `/api/users/behaviors/{userbehavior_id}/`.

    ## Update a Behavior Mapping.

    Updating a behavior mapping is currently not supported.

    ## Update a Behavior Mapping / Custom Triggers

    Behavior Mappings may be updated in order to set custom Triggers (aka
    reminders) for the associated behavior.

    To do this, send a PUT request to the detail url
    (`api/users/behaviors/{userbehavior_id}`) with the following information:

    * `custom_trigger_time`: The time at which the reminder should fire, in
      `hh:mm` format.
    * `custom_trigger_rrule`: A Unicode RFC 2445 string representing the days &
      frequencies at which the reminder should occur.

    ## Filtering

    UserBehaviors can be filtered using a querystring parameter. Currently,
    filtering is availble for Goals. You can filter by an ID or a slug.

    To retrieve all *UserBehavior*s that belong to a particular goal, use
    one of the following:

    * `/api/behaviors/?goal={goal_id}` or by slug
    * `/api/behaviors/?goal={goal_title_slug}`

    ## Additional information

    The Behaviors that a User has selected are also available through the
    `/api/users/` endpoint as a `behaviors` object on the user.

    Each results object also includes a `user_goals` object in addition to
    a `behavior` object. The `user_goals` object is a list of Goals in
    which the behavior belongs that have also be selected by the User. Related:
    [/api/users/goals/](/api/users/goals/).

    ----

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.UserBehavior.objects.published()
    serializer_class = serializers.UserBehaviorSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        # First, only expose content in Categories/Packages that are either
        # public or in which we've accepted the terms/consent form.
        self.queryset = models.UserBehavior.objects.accepted_or_public(self.request.user)

        # Now, filter on category or goal if necessary
        goal = self.request.GET.get('goal', None)
        self.queryset = self.queryset.filter(user__id=self.request.user.id)

        if goal is not None and goal.isnumeric():
            self.queryset = self.queryset.filter(behavior__goals__id=goal)
        elif goal is not None:
            self.queryset = self.queryset.filter(behavior__goals__title_slug=goal)
        return self.queryset

    def get_serializer(self, *args, **kwargs):
        """Ensure we pass `many=True` into the serializer if we're dealing
        with a list of items."""
        if isinstance(self.request.data, list):
            kwargs['many'] = True
        return super(UserBehaviorViewSet, self).get_serializer(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Only create objects for the authenticated user."""
        if isinstance(request.data, list):
            # We're creating multiple items
            for d in request.data:
                d['user'] = request.user.id
        else:
            request.data['user'] = request.user.id
        return super(UserBehaviorViewSet, self).create(request, *args, **kwargs)

    def _include_trigger(self, request, rrule, time):
        """Inserts a Trigger object into the request's payload"""
        if rrule and time:
            # Apparently these will always be lists, but for some reason the
            # rest framework plumbing doesn't actually convert them to their
            # primary values; And I can't override this in the Serializer subclass
            # because it fails before field-level validation is called
            # (e.g. validate_time or validate_rrule)
            if isinstance(rrule, list) and len(rrule) > 0:
                rrule = rrule[0]
            if isinstance(time, list) and len(time) > 0:
                time = time[0]

            obj = self.get_object()
            request.data['user'] = obj.user.id
            request.data['behavior'] = obj.behavior.id

            # Generate a name for the Trigger. MUST be unique.
            tname = obj.get_custom_trigger_name()
            try:
                trigger = models.Trigger.objects.get(user=obj.user, name=tname)
            except models.Trigger.DoesNotExist:
                trigger = None

            trigger_data = {
                'user_id': obj.user.id,
                'time': time,
                'name': tname,
                'rrule': rrule
            }
            trigger_serializer = serializers.CustomTriggerSerializer(
                instance=trigger,
                data=trigger_data
            )
            if trigger_serializer.is_valid(raise_exception=True):
                trigger = trigger_serializer.save()

            if hasattr(obj, 'custom_trigger'):
                obj.custom_trigger = trigger
                obj.save(update_fields=['custom_trigger'])
            request.data['custom_trigger'] = trigger
        return request

    def update(self, request, *args, **kwargs):
        """Allow setting/creating a custom trigger using only two pieces of
        information:

        * custom_trigger_rrule
        * custom_trigger_time

        """
        rrule = request.data.pop("custom_trigger_rrule", None)
        time = request.data.pop("custom_trigger_time", None)
        request = self._include_trigger(request, rrule, time)
        result = super(UserBehaviorViewSet, self).update(request, *args, **kwargs)
        return result


class UserActionViewSet(mixins.CreateModelMixin,
                        mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.DestroyModelMixin,
                        mixins.UpdateModelMixin,
                        DeleteMultipleMixin,
                        viewsets.GenericViewSet):
    """This endpoint represents a mapping between [Users](/api/users/) and
    [Actions](/api/actions/).

    GET requests to this page will simply list this mapping for the authenticated
    user.

    ## Fields

    This endpoint returns resources with the following fields.

    * `id`: A unique identifier for the `UserAction` mapping.
    * `user`: A unique identifier for the `User`
    * `action`: An object that represents the `Action` selected by the user
    * `behavior`: An object that represents the `Action`'s parent `Behavior`.
    * `next_reminder`: a date/time in the user's local timezone for the
      next push notification for this action (may be null if nothing is scheduled)
    * `custom_trigger`: An object that represent's the user's created `Trigger`,
      i.e. information about when notifications for this action should be sent.
    * `custom_triggers_allowed`: A boolean that indicates whether or not a user
      should be able to customize the reminders for this action.
    * `primary_goal`: The goal under which the user selected this action.
    * `primary_category`: The primary category associated with this action.
    * `created_on`: Time at which the user selected this item.

    ## Adding a Action

    To associate a Action with a User, POST to `/api/users/actions/` with the
    following data (the action the user is selecting, and (optionally) the
    parent goal for the action).

        {'action': ACTION_ID, 'primary_goal': GOAL_ID}

    ## Adding multiple Actions in one request

    This endpoint also allows you to associate multiple actions with a user
    in a single request. To do this, POST an array of action IDs, e.g.:

        [
            {'action': 3, 'primary_goal': GOAL_ID},
            {'action': 4, 'primary_goal': GOAL_ID},
            {'action': 5, 'primary_goal': GOAL_ID}
        ]

    ## Removing multiple Actions in one request.

    This endpoint also allows you to remove  multiple instances of the
    user-to-action association. Tod do this, send a DELETE request with
    an array of `useraction` IDs, e.g.:

        [
            {'useraction': 3},
            {'useraction': 4},
            {'useraction': 5}
        ]

    ## Viewing the Action data

    Additional information for the Action mapping is available at
    `/api/users/actions/{useraction_id}/`. In this case, `{useraction_id}`
    is the database id for the mapping between a user and a action.

    ## Removing a Action from the user's list.

    Send a DELETE request to the useraction mapping endpoint:
    `/api/users/actions/{useraction_id}/`.

    ## Update a Action Mapping / Custom Triggers

    Action Mappings may be updated in order to set custom Triggers (aka
    reminders) for the associated action.

    To do this, send a PUT request to the detail url (`api/users/actions/{useraction_id}`)
    with the following information:

    * `custom_trigger_time`: The time at which the reminder should fire, in
      `hh:mm` format, in the user's local time.
    * `custom_trigger_date`: (optional). For a one-time reminder, the this can
      include a date string (yyyy-mm-dd) to define the date at which a reminder
      should next fire. The date should be relative to the user's local time.
    * `custom_trigger_rrule`: A Unicode RFC 2445 string representing the days &
      frequencies at which the reminder should occur.

    ## Filtering

    UserActions can be filtered using a querystring parameter. Currently,
    filtering is availble for Goals, Behaviors, Actions, and for Actions
    whose notification is scheduled during the current day.

    To filter for actions scheduled _today_, use the following:

    * `/api/users/actions/?today=1`

    For the following examples, you may filter using an ID or a slug.

    To retrieve all *UserAction*s that belong to a particular Goal, use
    one of the following:

    * `/api/users/actions/?goal={goal_id}` or by slug
    * `/api/users/actions/?goal={goal_title_slug}`

    To retrieve all *UserAction*s that belong to a particular Behavior, use
    one of the following:

    * `/api/users/actions/?behavior={behavior_id}` or by slug
    * `/api/users/actions/?behavior={behavior_title_slug}`

    To retrive all *UserActions*s that belong to a particular Action, use one
    of the following:

    * `/api/users/actions/?action={action_id}` or by slug
    * `/api/users/actions/?action={action_title_slug}`

    **NOTE**: Action titles are not unique, so filtering by the `title_slug`
    may return a number of results.

    ## Additional information

    The Actions that a User has selected are also available through the
    `/api/users/` endpoint as a `actions` object on the user.

    ## Completing Actions (or not)

    A User may wish to indicate that they have performed (or completed),
    dismissed, snoozed, or have decided not to complete an action. To save this
    information:

    * send a POST request to `/api/users/actions/{useraction_id}/complete/`
      with a body containing a `state` and an optional `length`; these values
      tell us how the user responded to the action, and how long they snoozed
      the action (if that's what they did).

            {
                'state': 'snoozed',   # or 'completed', 'uncompleted', 'dismissed'
                'length': '1hr'         # or  "1d", "custom", "location"
            }

    * A 200 response indicates that the action has been updated or created. If
      updated, the response will be: `{updated: <object_id>}`, if created:
      `{created: <object_id>}`.

    ----

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.UserAction.objects.published()
    serializer_class = serializers.UserActionSerializer
    permission_classes = [IsOwner]

    def get_serializer_class(self):
        """
        XXX: I want to user our regular serializer for PUT & POST requests,
        but I want to use a faster serializer that users the UserAction's
        pre-rendered fields for GET requests.

        """
        if self.request.method == "GET":
            return serializers.ReadOnlyUserActionSerializer
        return self.serializer_class

    def get_queryset(self):
        # First, only expose content in Categories/Packages that are either
        # public or in which we've accepted the terms/consent form.
        self.queryset = models.UserAction.objects.accepted_or_public(self.request.user)

        # Now, filter on category or goal if necessary
        filter_on_today = bool(self.request.GET.get('today', False))
        goal = self.request.GET.get('goal', None)
        behavior = self.request.GET.get('behavior', None)
        action = self.request.GET.get('action', None)

        if goal is not None and goal.isnumeric():
            self.queryset = self.queryset.filter(action__behavior__goals__id=goal)
        elif goal is not None:
            self.queryset = self.queryset.filter(action__behavior__goals__title_slug=goal)

        if behavior is not None and behavior.isnumeric():
            self.queryset = self.queryset.filter(action__behavior__id=behavior)
        elif behavior is not None:
            self.queryset = self.queryset.filter(action__behavior__title_slug=behavior)
        if action is not None and action.isnumeric():
            self.queryset = self.queryset.filter(action__id=action)
        elif action is not None:
            self.queryset = self.queryset.filter(action__title_slug=action)

        if filter_on_today:
            today = local_day_range(self.request.user)
            self.queryset = self.queryset.filter(
                Q(prev_trigger_date__range=today) |
                Q(next_trigger_date__range=today)
            )

        return self.queryset

    def get_serializer(self, *args, **kwargs):
        """Ensure we pass `many=True` into the serializer if we're dealing with
        a list of items."""
        if isinstance(self.request.data, list):
            kwargs['many'] = True
        return super(UserActionViewSet, self).get_serializer(*args, **kwargs)

    def list(self, request, *args, **kwargs):
        if request.GET.get('today', False):
            # This is probably the morning check-in
            metric('viewed-useractions', category="User Interactions")
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        if request.GET.get('today', False):
            # This is probably the morning check-in
            metric('viewed-useractions', category="User Interactions")
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Only create objects for the authenticated user."""
        if isinstance(self.request.data, list):
            # We're creating multiple items
            for d in request.data:
                d['user'] = request.user.id
        else:
            # We're creating a single item
            request.data['user'] = request.user.id
        return super(UserActionViewSet, self).create(request, *args, **kwargs)

    def _include_trigger(self, request, trigger_rrule, trigger_time, trigger_date):
        """Includes a Trigger object into the request's payload; That means,
        if we're updating a UserAction, but the Custom Trigger is getting
        created or updated, we'll make that change, here, then include the
        Trigger in as part of the request.

        This method looks for an existing Trigger object, and creates one if
        it doesn't exist.

        """
        # It's OK if the rrule, time, date are empty/none.

        # Apparently these will always be lists, but for some reason the
        # rest framework plumbing doesn't actually convert them to their
        # primary values; And I can't override this in the Serializer subclass
        # because it fails before field-level validation is called
        # (e.g. validate_trigger_time or validate_trigger_rrule)
        if isinstance(trigger_rrule, list) and len(trigger_rrule) > 0:
            trigger_rrule = trigger_rrule[0]
        if isinstance(trigger_time, list) and len(trigger_time) > 0:
            trigger_time = trigger_time[0]
        if isinstance(trigger_date, list) and len(trigger_date) > 0:
            trigger_date = trigger_date[0]

        ua = self.get_object()
        request.data['user'] = ua.user.id
        request.data['action'] = ua.action.id

        # Generate a name for the Trigger. MUST be unique.
        tname = ua.get_custom_trigger_name()
        try:
            trigger = models.Trigger.objects.get(user=ua.user, name=tname)
        except models.Trigger.DoesNotExist:
            trigger = None

        trigger_data = {
            'user_id': ua.user.id,
            'time': trigger_time,
            'name': tname,
            'rrule': trigger_rrule,
            'date': trigger_date
        }
        trigger_serializer = serializers.CustomTriggerSerializer(
            instance=trigger,
            data=trigger_data
        )
        if trigger_serializer.is_valid(raise_exception=True):
            trigger = trigger_serializer.save()
        if hasattr(ua, 'custom_trigger'):
            ua.custom_trigger = trigger
            ua.save(update_fields=['custom_trigger'])
        request.data['custom_trigger'] = trigger
        return request

    def _has_custom_trigger_params(self, params):
        """Before we update/create a custom trigger, let's check to see if
        the request actually includes any of the trigger parameters."""
        return any([
            'custom_trigger_rrule' in params,
            'custom_trigger_time' in params,
            'custom_trigger_date' in params]
        )

    def update(self, request, *args, **kwargs):
        """Allow setting/creating a custom trigger using only two pieces of
        information:

        * custom_trigger_rrule
        * custom_trigger_time
        * custom_trigger_date

        """
        if self._has_custom_trigger_params(request.data.keys()):
            request = self._include_trigger(
                request,
                trigger_rrule=request.data.pop("custom_trigger_rrule", None),
                trigger_time=request.data.pop("custom_trigger_time", None),
                trigger_date=request.data.pop("custom_trigger_date", None)
            )
        result = super(UserActionViewSet, self).update(request, *args, **kwargs)
        return result

    @detail_route(methods=['post'], permission_classes=[IsOwner], url_path='complete')
    def complete(self, request, pk=None):
        """"Allow a user to complete their action. If the POST request has no
        body, we assume they're marking it as `completed`, otherwise we update
        based on the given `state` field."""
        try:
            useraction = self.get_object()
            state = request.data.get('state', 'completed')
            updated = False
            try:
                # Keep 1 record per day
                now = timezone.now()
                uca = models.UserCompletedAction.objects.filter(
                    created_on__year=now.year,
                    created_on__month=now.month,
                    created_on__day=now.day
                ).get(
                    user=useraction.user,
                    action=useraction.action,
                    useraction=useraction
                )
                uca.state = state
                uca.save()
                updated = True
            except models.UserCompletedAction.DoesNotExist:
                uca = models.UserCompletedAction.objects.create(
                    user=useraction.user,
                    action=useraction.action,
                    useraction=useraction,
                    state=state
                )

            if state == 'snoozed':
                metric("snooze-{0}".format(request.data.get('length', 'undefined')), category='Snoozed Reminders')

            if updated:
                data = {'updated': uca.id}
                status_code = status.HTTP_200_OK
            else:
                data = {'created': uca.id}
                status_code = status.HTTP_201_CREATED
            return Response(data=data, status=status_code)

        except Exception as e:
            return Response(
                data={'error': "{0}".format(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserCategoryViewSet(mixins.CreateModelMixin,
                          mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.DestroyModelMixin,
                          DeleteMultipleMixin,
                          viewsets.GenericViewSet):
    """This endpoint represents a mapping between [Users](/api/users/) and
    [Categories](/api/categories/).

    GET requests to this page will simply list this mapping for the authenticated
    user.

    ## Fields

    This endpoint returns resources with the following fields.

    * `id`: A unique identifier for the `UserCategory` mapping.
    * `user`: A unique identifier for the `User`
    * `category`: An object that represents the `Category` selected by the user
    * `user_goals_count`: the number of child Goals that the user has selected
      that are contained in this category.
    * `user_goals`: An array of `Goal` objects selected by the user.
    * `created_on`: Time at which the user selected the Category.
    * `progress_value`: The user's self-reported progress toward goals in this
      category.
    * `custom_triggers_allowed`: A boolean that indicates whether or not a user
      should be able to customize the reminders beneath this content

    ## Adding a Category

    To associate a Category with a User, POST to `/api/users/categories/` with the
    following data:

        {'category': CATEGORY_ID}

    ## Adding multiple Categories in one request

    This endpoint also allows you to associate multiple categories with a user
    in a single request. To do this, POST an array of category IDs, e.g.:

        [
            {'category': 3},
            {'category': 4},
            {'category': 5}
        ]

    ## Removing multiple Categories in one request.

    This endpoint also allows you to remove  multiple instances of the
    user-to-category association. Tod do this, send a DELETE request with
    an array of `usercategory` IDs, e.g.:

        [
            {'usercategory': 3},
            {'usercategory': 4},
            {'usercategory': 5}
        ]

    ## Viewing the Category data

    Additional information for the Category mapping is available at
    `/api/users/categories/{usercategory_id}/`. In this case, `{usercategory_id}`
    is the database id for the mapping between a user and a category

    ## Removing a Category from the user's list.

    Send a DELETE request to the usercategory mapping endpoint:
    `/api/users/categories/{usercategory_id}/`.

    ## Update a Category Mapping.

    Updating a category mapping is currently not supported.

    ## Additional information

    The Categories that a User has selected are also available through the
    `/api/users/` endpoint as a `categories` object on the user.

    Each results object also includes a `user_goals` object in addition to
    a `category` object. The `user_goals` object is a list of Goals that are
    contained in the Category, and have also be selected by the User. Related:
    [/api/users/goals/](/api/users/goals/).

    ----

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.UserCategory.objects.published()
    serializer_class = serializers.UserCategorySerializer

    def get_queryset(self):
        return models.UserCategory.objects.accepted_or_public(user=self.request.user)

    def get_serializer(self, *args, **kwargs):
        """Ensure we pass `many=True` into the serializer if we're dealing
        with a list of items."""
        if isinstance(self.request.data, list):
            kwargs['many'] = True
        return super(UserCategoryViewSet, self).get_serializer(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Only create objects for the authenticated user."""
        if isinstance(request.data, list):
            # We're creating multiple items.
            for d in request.data:
                d['user'] = request.user.id
        else:
            # We're creating a single items.
            request.data['user'] = request.user.id
        return super(UserCategoryViewSet, self).create(request, *args, **kwargs)


class GoalProgressViewSet(mixins.CreateModelMixin,
                          mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.UpdateModelMixin,
                          viewsets.GenericViewSet):
    """This endpoint allows a user to record and/or update their daily check-in
    progress toward a Goal, and retrieve a history of that progress.

    Each item in this result contains a number of fields. The basic ones are:

    * `id`: The object's unique ID.
    * `goal`: The ID of the related Goal.
    * `usergoal`: The ID of the `UserGoal` (user-to-goal mapping)
    * `reported_on`: The date/time on which this object was initially created.

    The following fields were used in a (now deprecated) daily 3-scale behavior
    check-in:

    * `current_score`: aggregate value for the user's behaviors in this goal.
    * `current_total`: sum of user's check-in values.
    * `max_total`: maximum possible value

    The following are the new daily check-in values:

    * `daily_checkin`: The user's daily check-in value for this goal.
    * `weekly_checkin`: Average over the past 7 days.
    * `monthly_checkin`: Average over the past 30 days.

    The following are stats calculated based on actions that the user has
    completed. The weekly values are average over 7 days while the rest (e.g.
    `action_progress`) are averaged over 30 days:

    * `daily_actions_total`: The total number of Actions the user had scheduled
      within this goal.
    * `daily_actions_completed`: The number of actions completed.
    * `daily_action_progress`: Percentage of completed vs. incomplete (as a decimal)
    * `daily_action_progress_percent`: Percentage of completed vs. incomplete
      (as an integer)
    * `weekly_actions_total`
    * `weekly_actions_completed`
    * `weekly_action_progress`
    * `weekly_action_progress_percent`
    * `actions_total`
    * `actions_completed`
    * `action_progress`
    * `action_progress_percent`

    ## Saving Progress

    To record progress toward a goal, send a POST request containing the
    following information:

    * `goal`: The ID for the Goal.
    * `daily_checkin`: An integer value in the range 1-5 (inclusive)

    This will create a new GoalProgress snapshot. _However_, if an instance
    of a GoalProgress alread exists for the day in which this data is POSTed,
    that instance will be updated (so that there _should_ only be one of these
    per day).

    ## Updating Progress

    You may also update a GoalProgress by sending a PUT request to
    `/api/users/goals/progress/{id}/` containing the same information that
    you'd use to create a Goalprogress.

    ## Getting Average Progress

    You may set a GET request to the
    [/api/users/goals/progress/average/](/api/users/goals/progress/average/]
    endpoint to retrive an average daily and weekly progress. These values
    are averaged over the past 7 days, and are compared with a given `current`
    value.

    For example, if the user's current goal progress feed back average is `5`,
    send the following GET request:

        /api/users/goals/progress/average/?current=5

    The full result of this endpoint contains the following information:

    * `daily_checkin_avg` - Average of _all_ GoalProgress.daily_checkin
      values for the user for _today_.
    * `weekly_checkin_avg` - Average GoalProgress.daily_checkin values over
      the past 7 days.
    * `better`: True if current is > daily_checkin_avg, False otherwise.
    * `text`: Some display text based on the value of `better`.

    ----

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.GoalProgress.objects.all()
    serializer_class = serializers.GoalProgressSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return self.queryset.filter(user__id=self.request.user.id)

    def _parse_request_data(self, request):
        """This method does a few things to modify any request data:

        - ensure we only create objects for the authenticated user
        - add the id of the GoalProgress if we already have one for today
        - if a Goal id is submitted, try to include the UserGoal id

        """
        if not request.user.is_authenticated():
            return request

        # Set the authenticated user's ID
        request.data['user'] = request.user.id

        if request.method == "POST":
            # If a goal is provided, attempt to retrieve the UserGoal object
            if 'goal' in request.data and 'usergoal' not in request.data:
                try:
                    goal = request.data.get('goal', [])
                    request.data['usergoal'] = models.UserGoal.objects.filter(
                        user=request.user,
                        goal__id=goal
                    ).values_list('id', flat=True)[0]
                except (models.UserGoal.DoesNotExist, IndexError):
                    pass  # Creating will fail

            # If we already have a GoalProgress for "today", include its ID
            try:
                today = local_day_range(self.request.user)
                params = {
                    'user': request.user.id,
                    'reported_on__range': today,
                }
                if 'usergoal' in request.data:
                    params['usergoal'] = request.data['usergoal']
                if 'goal' in request.data:
                    params['goal'] = request.data['goal']
                qs = models.GoalProgress.objects.filter(**params)
                request.data['id'] = qs.latest().id
            except models.GoalProgress.DoesNotExist:
                pass
        return request

    def update(self, request, *args, **kwargs):
        request = self._parse_request_data(request)
        metric('updated-goal-progress', category="User Interactions")
        return super().update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        request = self._parse_request_data(request)

        # If we've got a GoalProgress ID, we need to update instead of create
        if 'id' in request.data:
            gp = models.GoalProgress.objects.get(id=request.data['id'])
            gp.daily_checkin = request.data['daily_checkin']
            gp.save()
            data = self.serializer_class(gp).data
            return Response(data=data, status=status.HTTP_200_OK)
        metric('created-goal-progress', category="User Interactions")
        return super().create(request, *args, **kwargs)

    @list_route(permission_classes=[IsOwner], url_path='average')
    def average(self, request, pk=None):
        """Returns some average progress values for the user + some feedback
        text comparing any given `current` value with the daily average.

        Accepts a GET parameter for `current`: The user's current daily
        checking average (i.e. the average value for all goals that the user
        is currently checking in.)

        Returns:

        * `daily_checkin_avg` - Average of _all_ GoalProgress.daily_checkin
          values for the user for _today_.
        * `weekly_checkin_avg` - Average GoalProgress.daily_checkin values over
          the past 7 days.
        * `better`: True if current is > daily_checkin_avg, False otherwise.
        * `text`: Some display text based on the value of `better`.

        """
        if not request.user.is_authenticated():
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            user = request.user
            today = local_day_range(self.request.user)
            week_threshold = timezone.now() - timedelta(days=7)
            current = int(request.GET.get('current', 0))

            # Average for Today's progress; all goals.
            daily = models.GoalProgress.objects.filter(
                daily_checkin__gt=0,
                reported_on__range=today,
                user=user
            ).aggregate(Avg('daily_checkin'))
            daily = round((daily.get('daily_checkin__avg', 0) or 0), 2)

            # Average of daily checkins for all goals this week
            weekly = models.GoalProgress.objects.filter(
                daily_checkin__gt=0,
                reported_on__gte=week_threshold,
                user=user
            ).aggregate(Avg('daily_checkin'))
            weekly = round((weekly.get('daily_checkin__avg', 0) or 0), 2)

            better = current >= daily
            if better:
                text = settings.CHECKIN_BETTER
            else:
                text = settings.CHECKIN_WORSE
            data = {
                'daily_checkin_avg': daily,
                'weekly_checkin_avg': weekly,
                'better': better,
                'text': text,
            }
            status_code = status.HTTP_200_OK
            return Response(data=data, status=status_code)
        except Exception as e:
            return Response(
                data={'error': "{0}".format(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class BehaviorProgressViewSet(mixins.CreateModelMixin,
                              mixins.ListModelMixin,
                              mixins.RetrieveModelMixin,
                              mixins.UpdateModelMixin,
                              viewsets.GenericViewSet):
    """ This endpoint allows a user to record their daily 'self-assessed'
    progress toward a Behavior, and retrieve a history of that progress.

    This model also contains daily aggregates of completed actions that are
    children of the behavior.

    GET requests will return the following information for an authenticated user:

    * `id`: Unique ID for a `BehaviorProgress` object.
    * `user`: ID of the authenticated user.
    * `user_behavior`: ID of the associated `UserBehavior` (User-to-Behavior mapping)
    * `status`: Value of their progress, in the range of 1-3
    * `status_display`: Human-readable status of the user's progress.
    * `daily_actions_total`: The total number of actions contained within the
      Behavior that were scheduled for the day.
    * `daily_actions_complete`:  The number of actions within the Behavior that
      were completed during the day.
    * `daily_action_progress`: The percentage of actions completed. Calculated
      vial `daily_actions_completed` / `daily_actions_total`.
    * `daily_action_progress_percent`: The same as `daily_action_progress`, but
      as an integer percent instead of a decimal.
    * `reported_on`: Date on which progress was initially reported.

    ## Saving Progress

    To record progress toward a behavior, send a POST request containing the
    following information:

    * `status`: A numerical value, 1 for "Off Course", 2 for "Seeking", and 3
      for "On Course".
    * `behavior`: The ID for the Behavior. Optional if `user_behavior` is provided
    * `user_behavior`: The ID for the `UserBehavior` instance (the mapping
      between a User and a Behavior). Optional if `behavior` is provided.

    This will create a new BehaviorProgress snapshot. _However_, if an instance
    of a BehaviorProgress alread exists for the day in which this data is POSTed,
    that instance will be updated (so that there _should_ only be one of these
    per day).

    ## Updating Progress

    You may also send a PUT request to `/api/users/behaviors/progress/{id}/`
    with the following information to update an existing `BehaviorProgress`
    instance:

    * `status`: A numerical value, 1 for "Off Course", 2 for "Seeking", and 3
      for "On Course".
    * `user_behavior`: The ID for the `UserBehavior` instance (the mapping
      between a User and a Behavior).

    ----

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.BehaviorProgress.objects.all()
    serializer_class = serializers.BehaviorProgressSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return self.queryset.filter(user__id=self.request.user.id)

    def _parse_request_data(self, request):
        """This method does a few things to modify any request data:

        - ensure we only create objects for the authenticated user
        - add the id of the BehaviorProgress if we already have one for today
        - if a Behavior id is submitted, try to include the UserBehavior id

        """
        if not request.user.is_authenticated():
            return request

        # Set the authenticated user's ID
        request.data['user'] = request.user.id

        # If a behavior is provided, attempt to retrieve the UserBehavior object
        if request.method == "POST":
            if 'behavior' in request.data and 'user_behavior' not in request.data:
                try:
                    behavior = request.data.pop('behavior', [])
                    if isinstance(behavior, list):
                        behavior = behavior[0]
                    request.data['user_behavior'] = models.UserBehavior.objects.filter(
                        user=request.user,
                        behavior__id=behavior
                    ).values_list('id', flat=True)[0]
                except (models.UserBehavior.DoesNotExist, IndexError):
                    pass  # Creating will fail

            # If we already have a BehaviorProgress for "today", include its ID
            try:
                now = timezone.now()
                params = {
                    'user': request.user.id,
                    'reported_on__year': now.year,
                    'reported_on__month': now.month,
                    'reported_on__day': now.day,
                }
                if 'user_behavior' in request.data:
                    params['user_behavior'] = request.data['user_behavior']
                else:
                    params['behavior'] = request.data['behavior']
                qs = models.BehaviorProgress.objects.filter(**params)
                request.data['id'] = qs.latest().id
            except models.BehaviorProgress.DoesNotExist:
                pass

        return request

    def update(self, request, *args, **kwargs):
        request = self._parse_request_data(request)
        return super().update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        request = self._parse_request_data(request)

        # If we've got a BehaviorProgress ID, we need to update instead of create
        if 'id' in request.data:
            bp = models.BehaviorProgress.objects.get(id=request.data['id'])
            bp.status = request.data['status']
            bp.save()
            data = self.serializer_class(bp).data
            return Response(data=data, status=status.HTTP_200_OK)
        return super().create(request, *args, **kwargs)


class PackageEnrollmentViewSet(mixins.ListModelMixin,
                               mixins.RetrieveModelMixin,
                               mixins.UpdateModelMixin,
                               viewsets.GenericViewSet):
    """ This endpoint allows a user retreive and update their enrollment
    information for "packaged content".

    GET requests will return the following information for an authenticated
    user:

    * `user`: ID of the authenticated user.
    * `accepted`: Whether or not the user has accepted the enrollment.
    * `updated_on`: Date at which this enrollment was last updated.
    * `enrolled_on`: Date on which the user was enrolled.
    * `category`: the category / package in which the user is enrolled. This
      representation of a category is slightly different from others in the API,
      because it includes both markdown and html versions of consent fields:
      `consent_summary`, `html_consent_summary`, `consent_more`, and
      `html_consent_more`.
    * `goals`: an array of goals that are included in this category / package

    ## Accepting the Enrollment

    When users are enrolled into packaged content, they must indeicate their
    acceptance of the _consent_ (`consent_summary`, `consent_more`). To
    update a user's acceptance, send a PUT request to the detail endpoint
    for a PackentEnrollment.

    PUT to `/api/users/packages/{id}/` with:

        {'accepted': True}

    This will indicate they've accepted the terms of the enrollment, and the
    packaged content will be available with the rest of the content.

    ----

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.PackageEnrollment.objects.all()
    serializer_class = serializers.PackageEnrollmentSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return self.queryset.filter(user__id=self.request.user.id)

    def update(self, request, *args, **kwargs):
        """ONLY allow the user to change their acceptance of this item.

        * accept: A Boolean value.

        """
        obj = self.get_object()
        request.data['user'] = request.user.id
        request.data['category'] = obj.category.id
        result = super().update(request, *args, **kwargs)

        # Check the old object and refresh it to see if the user just accepted;
        # if so, we need to call .accept(), so they get enrolled properly
        new_obj = self.get_object()
        if not obj.accepted and new_obj.accepted:
            new_obj.accept()
        return result


class SearchViewSet(HaystackViewSet):
    """This endpoint lists results from our Search Index, which contains content
    from [Goals](/api/goals/) and [Actions](/api/actions/).

    ## Searching

    To search this content, simply send a GET request with a `q` parameter
    containing your search terms. For example:

        {'q': 'wellness'}

    A GET request without a search term will return all Goals indexed.

    ## Results

    A paginated list of results will be returned, and each result will contain
    the following attributes:

    * `id`: The ID of the object represented
    * `object_type`: A lowercase string representing the type of object
      (currently this will always be `goal`)
    * `title`: The title of the object.
    * `description`: The full description of the object.
    * `updated_on`: The date/time on which the object was last updated.
    * `text`: The full text stored in the search index. This is the content
      against which search is performed.
    * `highlighted`: A string containing html-highlighted matches. The
      highlighted keywords are wrapped with `<em>` tags.

    """
    index_models = [models.Goal]
    serializer_class = serializers.SearchSerializer
    filter_backends = [HaystackHighlightFilter]

    def list(self, request, *args, **kwargs):
        for query in request.GET.getlist('q'):
            # Split all search terms and flatten into a single list
            for term in query.split():
                if len(term) > 2:
                    metric('q={}'.format(term), category='Search Terms')
        return super().list(request, *args, **kwargs)
