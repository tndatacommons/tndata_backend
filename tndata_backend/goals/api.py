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
from utils.mixins import VersionedViewSetMixin

from . import models
from . import settings
from . serializers import v1, v2
from . mixins import DeleteMultipleMixin


class IsOwner(permissions.BasePermission):
    """Only allow owners of an object to view/edit it."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class CategoryViewSet(VersionedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for public Categories. See the api_docs/ for more info"""
    queryset = models.Category.objects.published()
    serializer_class_v1 = v1.CategorySerializer
    serializer_class_v2 = v2.CategorySerializer
    docstring_prefix = "goals/api_docs"


class GoalViewSet(VersionedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for public Goals. See the api_docs/ for more info"""
    queryset = models.Goal.objects.published()
    serializer_class_v1 = v1.GoalSerializer
    serializer_class_v2 = v2.GoalSerializer
    docstring_prefix = "goals/api_docs"

    def get_queryset(self):
        if 'category' in self.request.GET:
            self.queryset = self.queryset.filter(
                categories__id=self.request.GET['category']
            )
        return self.queryset


class TriggerViewSet(VersionedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for Triggers. See the api_docs/ for more info"""
    queryset = models.Trigger.objects.default()
    serializer_class_v1 = v1.TriggerSerializer
    serializer_class_v2 = v2.TriggerSerializer
    docstring_prefix = "goals/api_docs"


class BehaviorViewSet(VersionedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for public Behaviors. See the api_docs/ for more info"""
    queryset = models.Behavior.objects.published()
    serializer_class_v1 = v1.BehaviorSerializer
    serializer_class_v2 = v2.BehaviorSerializer
    docstring_prefix = "goals/api_docs"

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


class ActionViewSet(VersionedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for public Actions. See the api_docs/ for more info"""
    queryset = models.Action.objects.published()
    serializer_class_v1 = v1.ActionSerializer
    serializer_class_v2 = v2.ActionSerializer
    docstring_prefix = "goals/api_docs"

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


class UserGoalViewSet(VersionedViewSetMixin,
                      mixins.CreateModelMixin,
                      mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.DestroyModelMixin,
                      DeleteMultipleMixin,
                      viewsets.GenericViewSet):
    """ViewSet for UserGoals. See the api_docs/ for more info"""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.UserGoal.objects.published()
    serializer_class_v1 = v1.UserGoalSerializer
    serializer_class_v2 = v2.UserGoalSerializer
    docstring_prefix = "goals/api_docs"
    permission_classes = [IsOwner]

    def get_serializer_class(self):
        """
        XXX: I want to user our regular serializer for PUT & POST requests,
        but I want to use a faster serializer that users the UserAction's
        pre-rendered fields for GET requests.

        """
        if self.request.method == "GET" and self.request.version == "1":
            return v1.ReadOnlyUserGoalSerializer
        return super().get_serializer_class()

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


class UserBehaviorViewSet(VersionedViewSetMixin,
                          mixins.CreateModelMixin,
                          mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.DestroyModelMixin,
                          mixins.UpdateModelMixin,
                          DeleteMultipleMixin,
                          viewsets.GenericViewSet):
    """ViewSet for UserBehaviors. See the api_docs/ for more info"""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.UserBehavior.objects.published()
    serializer_class_v1 = v1.UserBehaviorSerializer
    serializer_class_v2 = v2.UserBehaviorSerializer
    docstring_prefix = "goals/api_docs"
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
            trigger_serializer = v1.CustomTriggerSerializer(
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


class UserActionViewSet(VersionedViewSetMixin,
                        mixins.CreateModelMixin,
                        mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.DestroyModelMixin,
                        mixins.UpdateModelMixin,
                        DeleteMultipleMixin,
                        viewsets.GenericViewSet):
    """ViewSet for UserActions. See the api_docs/ for more info"""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.UserAction.objects.published()
    serializer_class_v1 = v1.UserActionSerializer
    serializer_class_v2 = v2.UserActionSerializer
    docstring_prefix = "goals/api_docs"
    permission_classes = [IsOwner]

    def get_serializer_class(self):
        """
        XXX: I want to user our regular serializer for PUT & POST requests,
        but I want to use a faster serializer that users the UserAction's
        pre-rendered fields for GET requests.

        """
        if self.request.method == "GET" and self.request.version == "1":
            return v1.ReadOnlyUserActionSerializer
        return super().get_serializer_class()

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

    def create_parent_objects(self, request):
        """If the request includes all 4: category, goal, behavior, action,
        let's try to get or create all of the user's objects at once.

        """
        # We'll *only* do this if we have all the necessary data.
        checks = [
            'category' in request.data and bool(request.data['category']),
            'goal' in request.data and bool(request.data['goal']),
            'behavior' in request.data and bool(request.data['behavior']),
            'action' in request.data and bool(request.data['action']),
        ]
        if all(checks):
            # NOTE: request.data.pop returns a list, and we have to look up
            # each object individually in order to Create them.
            cat_id = request.data.pop('category')[0]
            uc, _ = models.UserCategory.objects.get_or_create(
                user=request.user,
                category=models.Category.objects.filter(id=cat_id).first()
            )
            goal_id = request.data.pop('goal')[0]
            ug, _ = models.UserGoal.objects.get_or_create(
                user=request.user,
                goal=models.Goal.objects.filter(id=goal_id).first()
            )
            behavior_id = request.data.pop('behavior')[0]
            ub, _ = models.UserBehavior.objects.get_or_create(
                user=request.user,
                behavior=models.Behavior.objects.filter(id=behavior_id).first()
            )
            request.data['primary_category'] = cat_id
            request.data['primary_goal'] = goal_id
        return request

    def create(self, request, *args, **kwargs):
        """Only create objects for the authenticated user."""
        if isinstance(self.request.data, list):
            # We're creating multiple items
            for d in request.data:
                d['user'] = request.user.id
        else:
            # We're creating a single item
            request.data['user'] = request.user.id

        # look for action, category, behavior, goal objects, and add them;
        # otherwise, this doesn't really do anything.
        request = self.create_parent_objects(request)
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
        trigger_serializer = v1.CustomTriggerSerializer(
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


class UserCategoryViewSet(VersionedViewSetMixin,
                          mixins.CreateModelMixin,
                          mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.DestroyModelMixin,
                          DeleteMultipleMixin,
                          viewsets.GenericViewSet):
    """ViewSet for UserCategory. See the api_docs/ for more info"""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.UserCategory.objects.published()
    serializer_class_v1 = v1.UserCategorySerializer
    serializer_class_v2 = v2.UserCategorySerializer
    docstring_prefix = "goals/api_docs"

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


class GoalProgressViewSet(VersionedViewSetMixin,
                          mixins.CreateModelMixin,
                          mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.UpdateModelMixin,
                          viewsets.GenericViewSet):
    """ViewSet for GoalProgress. See the api_docs/ for more info"""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.GoalProgress.objects.all()
    serializer_class_v1 = v1.GoalProgressSerializer
    serializer_class_v2 = v2.GoalProgressSerializer
    docstring_prefix = "goals/api_docs"
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
            serializer_class = self.get_serializer_class()
            data = serializer_class(gp).data
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


class BehaviorProgressViewSet(VersionedViewSetMixin,
                              mixins.CreateModelMixin,
                              mixins.ListModelMixin,
                              mixins.RetrieveModelMixin,
                              mixins.UpdateModelMixin,
                              viewsets.GenericViewSet):
    """ViewSet for BehaviorProgress. See the api_docs/ for more info"""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.BehaviorProgress.objects.all()
    serializer_class_v1 = v1.BehaviorProgressSerializer
    serializer_class_v2 = v2.BehaviorProgressSerializer
    docstring_prefix = "goals/api_docs"
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

            serializer_class = self.get_serializer_class()
            data = serializer_class(bp).data
            return Response(data=data, status=status.HTTP_200_OK)
        return super().create(request, *args, **kwargs)


class PackageEnrollmentViewSet(VersionedViewSetMixin,
                               mixins.ListModelMixin,
                               mixins.RetrieveModelMixin,
                               mixins.UpdateModelMixin,
                               viewsets.GenericViewSet):
    """ViewSet for PackageEnrollment. See the api_docs/ for more info"""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.PackageEnrollment.objects.all()
    serializer_class_v1 = v1.PackageEnrollmentSerializer
    serializer_class_v2 = v2.PackageEnrollmentSerializer
    docstring_prefix = "goals/api_docs"
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

    def post(self, request, **kwargs):
        """HACK to route POST requests containing a PK to `accept`."""
        if 'pk' in kwargs:
            return self.accept(request, **kwargs)
        return self.http_method_not_allowed(request, **kwargs)

    @detail_route(methods=['post'], url_path='')
    def accept(self, request, pk=None):
        """ This method adds an additional endpoint that lets us update an
        instance of their PackageEnrollment via a POST request; this is a
        temporary fix for clients that don't send PUT requests to accept an
        enrollment.

        """
        package_enrollment = self.get_object()
        if request.data.get('accepted', False):
            serializer_class = self.get_serializer_class()
            srs = serializer_class(instance=package_enrollment)
            package_enrollment.accept()
            return Response(srs.data)
        msg = {'error': 'invalid data'}
        return Response(msg, status=status.HTTP_400_BAD_REQUEST)


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
    # NOTE: This viewset is not versioned; our VersionedViewSetMixin conflics
    # with the HaystackViewset superclass.
    index_models = [models.Goal]
    serializer_class = v1.SearchSerializer
    filter_backends = [HaystackHighlightFilter]

    def list(self, request, *args, **kwargs):
        for query in request.GET.getlist('q'):
            # Split all search terms and flatten into a single list
            for term in query.split():
                if len(term) > 2:
                    metric('q={}'.format(term), category='Search Terms')
        return super().list(request, *args, **kwargs)


class CustomGoalViewSet(VersionedViewSetMixin,
                        mixins.CreateModelMixin,
                        mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin,
                        mixins.DestroyModelMixin,
                        viewsets.GenericViewSet):
    """ViewSet for CustomGoals. See the api_docs/ for more info"""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.CustomGoal.objects.all()
    serializer_class_v1 = v1.CustomGoalSerializer
    serializer_class_v2 = v2.CustomGoalSerializer
    docstring_prefix = "goals/api_docs"
    permission_classes = [IsOwner]

    def get_queryset(self):
        if self.request.user.is_authenticated():
            return models.CustomGoal.objects.filter(user=self.request.user)
        return models.CustomGoal.objects.none()

    def create(self, request, *args, **kwargs):
        """Only create objects for the authenticated user."""
        request.data['user'] = request.user.id
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Allow users to update their custom goals."""
        request.data['user'] = request.user.id
        return super().update(request, *args, **kwargs)


class CustomActionViewSet(VersionedViewSetMixin,
                          mixins.CreateModelMixin,
                          mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.UpdateModelMixin,
                          mixins.DestroyModelMixin,
                          viewsets.GenericViewSet):
    """ViewSet for CustomActions. See the api_docs/ for more info"""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    serializer_class_v1 = v1.CustomActionSerializer
    serializer_class_v2 = v2.CustomActionSerializer
    docstring_prefix = "goals/api_docs"
    queryset = models.CustomAction.objects.all()
    permission_classes = [IsOwner]

    def get_queryset(self):
        if self.request.user.is_authenticated():
            return models.CustomAction.objects.filter(user=self.request.user)
        return models.CustomAction.objects.none()

    def create(self, request, *args, **kwargs):
        """Only create objects for the authenticated user."""
        request.data['user'] = request.user.id
        return super().create(request, *args, **kwargs)

    def _include_trigger(self, request, trigger_rrule, trigger_time, trigger_date):
        """Includes a Trigger object into the request's payload; That means,
        if we're updating a CustomAction, but the Trigger is getting
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

        customaction = self.get_object()
        # Generate a name for the Trigger
        tname = "CustomAction trigger for {}".format(customaction.id)
        try:
            trigger = customaction.custom_trigger
        except models.Trigger.DoesNotExist:
            trigger = None

        trigger_data = {
            'user_id': customaction.user.id,
            'time': trigger_time,
            'name': tname,
            'rrule': trigger_rrule,
            'date': trigger_date
        }
        trigger_serializer = v1.CustomTriggerSerializer(
            instance=trigger,
            data=trigger_data
        )
        if trigger_serializer.is_valid(raise_exception=True):
            trigger = trigger_serializer.save()

        if trigger and trigger.id:
            customaction.custom_trigger = trigger
            customaction.save(update_fields=['custom_trigger'])
            request.data['custom_trigger'] = trigger
        return request

    def _has_custom_trigger_params(self, params):
        """Before we update/create a custom trigger, let's check to see if
        the request actually includes any of the trigger parameters."""
        return any([
            'custom_trigger_rrule' in params,
            'custom_trigger_time' in params,
            'custom_trigger_date' in params
        ])

    def update(self, request, *args, **kwargs):
        """Allow users to update their custom goals, additionally allowing
        the following optional fields for creating trigger details:

        * custom_trigger_rrule
        * custom_trigger_time
        * custom_trigger_date

        These custom triggers which work just like in the
        UserActionViewSet.update method.

        """
        request.data['user'] = request.user.id
        if self._has_custom_trigger_params(request.data.keys()):
            request = self._include_trigger(
                request,
                trigger_rrule=request.data.pop("custom_trigger_rrule", None),
                trigger_time=request.data.pop("custom_trigger_time", None),
                trigger_date=request.data.pop("custom_trigger_date", None)
            )
        return super().update(request, *args, **kwargs)

    @detail_route(methods=['post'], permission_classes=[IsOwner], url_path='complete')
    def complete(self, request, pk=None):
        """"Allow a user to complete their custom action. If the POST request
        has no body, we assume they're marking it as `completed`, otherwise we
        update based on the given `state` field.

        NOTE: this api is meant to duplicate that of UserCompletedAction.complete

        """
        try:
            customaction = self.get_object()
            state = request.data.get('state', 'completed')
            updated = False
            try:
                # Keep 1 record per day
                now = timezone.now()
                ucca = models.UserCompletedCustomAction.objects.filter(
                    created_on__year=now.year,
                    created_on__month=now.month,
                    created_on__day=now.day
                ).get(
                    user=request.user,
                    customaction=customaction,
                    customgoal=customaction.customgoal,
                )
                ucca.state = state
                ucca.save()
                updated = True
            except models.UserCompletedCustomAction.DoesNotExist:
                ucca = models.UserCompletedCustomAction.objects.create(
                    user=request.user,
                    customaction=customaction,
                    customgoal=customaction.customgoal,
                    state=state
                )

            if state == 'snoozed':
                t = request.data.get('length', 'undefined')
                metric("snooze-{0}".format(t), category='Snoozed Reminders')

            if updated:
                data = {'updated': ucca.id}
                status_code = status.HTTP_200_OK
            else:
                data = {'created': ucca.id}
                status_code = status.HTTP_201_CREATED
            return Response(data=data, status=status_code)

        except Exception as e:
            if e.__class__.__name__ == 'Http404':
                return_status = status.HTTP_404_NOT_FOUND
            else:
                return_status = status.HTTP_400_BAD_REQUEST
            return Response(
                data={'error': "{0}".format(e)},
                status=return_status
            )

    @detail_route(methods=['post'], permission_classes=[IsOwner], url_path='feedback')
    def feedback(self, request, pk=None):
        """"Allow a user to create a related CustomActionFeedback object for
        this custom action.

        """
        error_msg = ''
        try:
            customaction = self.get_object()
            text = request.data.get('text', '')
            if text:
                caf = models.CustomActionFeedback.objects.create(
                    user=request.user,
                    customaction=customaction,
                    customgoal=customaction.customgoal,
                    text=text
                )
                data = {
                    'id': caf.id,
                    'user': caf.user.id,
                    'customgoal': caf.customgoal.id,
                    'customaction': caf.customaction.id,
                    'text': caf.text,
                    'created_on': caf.created_on
                }
                return Response(data=data, status=status.HTTP_201_CREATED)
            error_msg = "Text is required for a CustomActionFeedback object"
        except Exception as e:
            error_msg = "{0}".format(e)

        return Response(
            data={'error': error_msg},
            status=status.HTTP_400_BAD_REQUEST
        )
