from rest_framework import mixins, permissions, viewsets
from rest_framework.authentication import (
    SessionAuthentication, TokenAuthentication
)

from . mixins import DeleteMultipleMixin
from . import models
from . import serializers


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
    * description: A short description of this Category. May contain markdown.
    * icon_url: A URL for a square image. This is the category's Icon.
    * image_url: A URL for a larger image associated with the category. Use as the
      category's _hero_ image above each tab.
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
    * description: A short description for the goal. May contain markdown.
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

    **NOTE**: This is still a work in progress and subject to change.

    Triggers contain the following:

    * id: The unique database identifier for the trigger
    * name: A unique name for a trigger.
    * name_slug: A web-friendly version of the name.
    * trigger_type: Type of trigger; should be "time" or "place"
    * time: for "time" trigger types, the time at which an alert is sent.
    * location: Location information (for "place" type triggers)
    * recurrences: For "time" triggers, this is an iCalendar (rfc2445) format.
      This field is optional and may be null.
    * recurrences_display: human-readible information for `recurrences`
    * next: Date/Time for the next occurance of this trigger

    ## Trigger Endpoints

    Each trigger is available at an endpoint based on it's database ID: `/api/triggers/{id}/`.

    ----

    """
    # NOTE: Triggers are not very useful right now.
    #
    # The data model for this is incomplete. It should also provide:
    # - A way for a user to create their own triggers (reminders)?
    # - a location; for geo-based notifications.
    # - endpoints taht are *not* just read-only.

    queryset = models.Trigger.objects.all()
    serializer_class = serializers.TriggerSerializer


class BehaviorViewSet(viewsets.ReadOnlyModelViewSet):
    """A Behavior Sequence (aka a *Behavior*) is an abstract
    behavior as well as a potential container for concrete actions.

    Each Behavior object contains the following:

    * id: The unique database identifier for the behavior
    * title: A unique, Formal title. Use this to refer to this item.
    * title_slug: A url-friendly version of title.
    * description: A short description of the Behavior. May contain markdown.
    * more_info: Additional information displayed when the user drills down into the content.
    * external_resource = A link or reference to an outside resource necessary for adoption
    * default_trigger: A trigger/reminder for this behavior. See the
        (Trigger)[/api/triggers/] endpoint.
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
    * description: A short description of the Action. May contain markdown.
    * more_info: Additional information displayed when the user drills down into the content.
    * external_resource = A link or reference to an outside resource necessary for adoption
    * default_trigger: A trigger/reminder for this behavior. See the
        (Trigger)[/api/triggers/] endpoint.
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
    queryset = models.UserGoal.objects.all()
    serializer_class = serializers.UserGoalSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return self.queryset.filter(user__id=self.request.user.id)

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
                          DeleteMultipleMixin,
                          viewsets.GenericViewSet):
    """This endpoint represents a mapping between [Users](/api/users/) and
    [Behaviors](/api/behaviors/).

    GET requests to this page will simply list this mapping for the authenticated
    user.

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
    queryset = models.UserBehavior.objects.all()
    serializer_class = serializers.UserBehaviorSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return self.queryset.filter(user__id=self.request.user.id)

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


class UserActionViewSet(mixins.CreateModelMixin,
                        mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.DestroyModelMixin,
                        DeleteMultipleMixin,
                        viewsets.GenericViewSet):
    """This endpoint represents a mapping between [Users](/api/users/) and
    [Actions](/api/actions/).

    GET requests to this page will simply list this mapping for the authenticated
    user.

    ## Adding a Action

    To associate a Action with a User, POST to `/api/users/actions/` with the
    following data:

        {'action': ACTION_ID}

    ## Adding multiple Actions in one request

    This endpoint also allows you to associate multiple actions with a user
    in a single request. To do this, POST an array of action IDs, e.g.:

        [
            {'action': 3},
            {'action': 4},
            {'action': 5}
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

    ## Update a Action Mapping.

    Updating a action mapping is currently not supported.

    ## Additional information

    The Actions that a User has selected are also available through the
    `/api/users/` endpoint as a `actions` object on the user.

    ----

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.UserAction.objects.all()
    serializer_class = serializers.UserActionSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return self.queryset.filter(user__id=self.request.user.id)

    def get_serializer(self, *args, **kwargs):
        """Ensure we pass `many=True` into the serializer if we're dealing with
        a list of items."""
        if isinstance(self.request.data, list):
            kwargs['many'] = True
        return super(UserActionViewSet, self).get_serializer(*args, **kwargs)

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
    queryset = models.UserCategory.objects.all()
    serializer_class = serializers.UserCategorySerializer

    def get_queryset(self):
        return self.queryset.filter(user__id=self.request.user.id)

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


class BehaviorProgressViewSet(mixins.CreateModelMixin,
                              mixins.ListModelMixin,
                              mixins.RetrieveModelMixin,
                              viewsets.GenericViewSet):
    """ This endpoint allows a user to record their progress toward a Behavior,
    and retrieve a history of that progress.

    GET requests will return the following information for an authenticated
    user:

    * `user`: ID of the authenticated user.
    * `user_behavior`: ID of the associated `UserBehavior` (User-to-Behavior mapping)
    * `status`: Value of their progress, in the range of 1-3
    * `reported_on`: Date on which progress was reported.

    ## Saving Progress

    To record progress toward a behavior, send a POST request containing the
    following information:

    * `status`: A numerical value, 1 for "Off Course", 2 for "Seeking", and 3
      for "On Course".
    * `behavior`: The ID for the Behavior. Optional if `user_behavior` is provided
    * `user_behavior`: The ID for the `UserBehavior` instance (the mapping
      between a User and a Behavior). Optional if `behavior` is provided.

    ----

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.BehaviorProgress.objects.all()
    serializer_class = serializers.BehaviorProgressSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return self.queryset.filter(user__id=self.request.user.id)

    def create(self, request, *args, **kwargs):
        """Only create objects for the authenticated user."""
        request.data['user'] = request.user.id
        # If a behavior id provided, attempt to retrieve the UserBehavior object
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
        return super().create(request, *args, **kwargs)
