import waffle

from django.conf import settings as project_settings
from django.db.models import Q
from django.utils import timezone

from django_rq import job
from drf_haystack.viewsets import HaystackViewSet
from drf_haystack.filters import HaystackHighlightFilter
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.authentication import (
    SessionAuthentication, TokenAuthentication
)
from rest_framework.decorators import detail_route, list_route
from rest_framework.pagination import PageNumberPagination, _positive_int
from rest_framework.response import Response
from redis_metrics import metric

from utils.user_utils import local_day_range
from utils.mixins import VersionedViewSetMixin

from . import models
from . serializers import v1, v2
from . mixins import DeleteMultipleMixin
from . permissions import is_content_author
from . utils import pop_first


class PageSizePagination(PageNumberPagination):
    page_size_query_param = 'page_size'


class PublicViewSetPagination(PageNumberPagination):
    """This is a pagination class for publicly accessable, read-only viewsets
    (e.g. the content library). It enables the following:

    1. checks for a switch and then lowers the default page size
    2. enables a client-specified page size using the `page_size` query param

    """
    page_size = 5  # XXX: Smaller than the globally-specified page size.
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_page_size(self, request):
        if self.page_size_query_param:
            try:
                return _positive_int(
                    request.query_params[self.page_size_query_param],
                    strict=True,
                    cutoff=self.max_page_size
                )
            except (KeyError, ValueError):
                pass

        if waffle.switch_is_active("small-api-paging"):
            return self.page_size
        return project_settings.REST_FRAMEWORK.get('PAGE_SIZE', 25)


class IsOwner(permissions.IsAuthenticated):
    """Only allow owners of an object to view/edit it."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsContentAuthor(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return is_content_author(request.user)


class CategoryViewSet(VersionedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for public Categories. See the api_docs/ for more info"""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.Category.objects.published()
    serializer_class_v1 = v1.CategorySerializer
    serializer_class_v2 = v2.CategorySerializer
    pagination_class = PublicViewSetPagination
    docstring_prefix = "goals/api_docs"

    def _as_bool(self, request, field):
        """Attempt to pull the given field from a GET parameter as a boolean
        value. This method will return True, False, or None if the value was
        not set."""
        value = request.GET.get(field, None)
        if value is not None:
            try:
                value = bool(value)
            except ValueError:  # invalid value, so return None
                value = None
        return value

    def get_queryset(self):
        self.queryset = super().get_queryset()
        selected_by_default = self._as_bool(self.request, 'selected_by_default')
        featured = self._as_bool(self.request, 'featured')
        if selected_by_default is not None:
            self.queryset = self.queryset.filter(
                selected_by_default=selected_by_default)
        if featured is not None:
            self.queryset = self.queryset.filter(featured=featured)
        return self.queryset

    def retrieve(self, request, pk=None):
        """When an authenticated user requests a category by ID, we may need
        to check if the user has access to it (since it may be a package or
        a non-public category).

        If so, this will return details for the category, otherwise this
        method will call out to the superclass.

        """
        authed = request.user.is_authenticated()
        kwargs = {'category__pk': pk, 'user': request.user if authed else None}
        exists = models.UserCategory.objects.filter(**kwargs).exists()
        if authed and exists:
            obj = models.UserCategory.objects.get(**kwargs)
            srs = self.get_serializer_class()(obj.category)
            return Response(srs.data)
        return super().retrieve(request, pk=pk)


@job
def _enroll_user_in_goal(user, goal, category=None):
    goal.enroll(user, category)


class GoalViewSet(VersionedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for public Goals. See the api_docs/ for more info"""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.Goal.objects.published()
    serializer_class_v1 = v1.GoalSerializer
    serializer_class_v2 = v2.GoalSerializer
    pagination_class = PublicViewSetPagination
    docstring_prefix = "goals/api_docs"

    def get_queryset(self):
        if 'category' in self.request.GET:
            self.queryset = self.queryset.filter(
                categories__id=self.request.GET['category']
            )

        # We want to exclude values from this endpoint that the user has already
        # selected (if the user is authenticated AND we're hitting api v2)
        user = self.request.user
        if self.request.version == '2' and user.is_authenticated():
            chosen = user.usergoal_set.values_list('goal__id', flat=True)
            self.queryset = self.queryset.exclude(id__in=chosen)

        return self.queryset

    def retrieve(self, request, *args, **kwargs):
        """If we're dealing with an authenticated user, AND that user has
        selected the goal with the given ID, we should return some details
        (even if the goal is not in a public package."""
        if request.user.is_authenticated():
            ug = models.UserGoal.objects.filter(
                user=request.user,
                goal__id=kwargs.get('pk', None),
                goal__state='published'
            )
            if ug.exists():
                serializer = self.get_serializer(ug.get().goal)
                return Response(serializer.data)
        return super().retrieve(request, *args, **kwargs)

    @detail_route(methods=['post'],
                  permission_classes=[IsContentAuthor],
                  url_path='order')
    def set_order(self, request, pk=None):
        """Allow certin users to update Goals through the api; but only
        to set the order.

            /api/goals/<id>/order/

        """
        try:
            # NOTE: we can't use self.get_object() here, because we're allowing
            # users to change items that may not yet be published.
            seq = int(request.data.get('sequence_order'))
            num = models.Goal.objects.filter(pk=pk).update(sequence_order=seq)
            return Response(data={'updated': num}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                data={'error': "{0}".format(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @detail_route(methods=['post'],
                  permission_classes=[permissions.IsAuthenticated],
                  url_path='enroll')
    def enroll(self, request, pk=None):
        """Let a user enroll themselves in a goal.

            /api/goals/<id>/enroll/

        Requires that a user be authenticated, and the POST request should
        contain the following info:

        - category: ID  (ID for a primary category)

        """
        try:
            # NOTE: It should be save to use self.get_object() here,
            # this should only happen for published goals.
            goal = self.get_object()
            category = request.data.get('category', None)
            if category:
                category = models.Category.objects.get(pk=category)

            # Async enrollment because this could be slow
            _enroll_user_in_goal.delay(request.user, goal, category)

            msg = (
                "Your request has been scheduled and your goals should "
                "appear in your feed soon."
            )
            return Response(data={'message': msg}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                data={'error': "{0}".format(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class TriggerViewSet(VersionedViewSetMixin,
                     mixins.CreateModelMixin,
                     mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.DestroyModelMixin,
                     mixins.UpdateModelMixin,
                     viewsets.GenericViewSet):
    """ViewSet for Triggers. See the api_docs/ for more info"""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.Trigger.objects.none()
    serializer_class_v1 = v1.TriggerSerializer
    serializer_class_v2 = v2.TriggerSerializer
    pagination_class = PublicViewSetPagination
    docstring_prefix = "goals/api_docs"
    permission_classes = [IsOwner]

    def get_queryset(self):
        return models.Trigger.objects.for_user(self.request.user)

    def create(self, request, *args, **kwargs):
        """Only create objects for the authenticated user."""
        if not request.user.is_authenticated():
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)
        request.data['user'] = request.user.id
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)
        return super().update(request, *args, **kwargs)


class BehaviorViewSet(VersionedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for public Behaviors. See the api_docs/ for more info"""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.Behavior.objects.published()
    serializer_class_v1 = v1.BehaviorSerializer
    serializer_class_v2 = v2.BehaviorSerializer
    pagination_class = PublicViewSetPagination
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

        # WE Want to exclude values from this endpoint that the user has already
        # selected (if the user is authenticated AND we're hitting api v2)
        user = self.request.user
        if self.request.version == '2' and user.is_authenticated():
            chosen = user.userbehavior_set.values_list('behavior__id', flat=True)
            self.queryset = self.queryset.exclude(id__in=chosen)

        return self.queryset

    @detail_route(methods=['post'],
                  permission_classes=[IsContentAuthor],
                  url_path='order')
    def set_order(self, request, pk=None):
        """Allow certin users to update Behaviors through the api; but only
        to set the order.

            /api/behaviors/<id>/order/

        """
        try:
            # NOTE: we can't use self.get_object() here, because we're allowing
            # users to change items that may not yet be published.
            seq = int(request.data.get('sequence_order'))
            num = models.Behavior.objects.filter(pk=pk).update(sequence_order=seq)
            return Response(data={'updated': num}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                data={'error': "{0}".format(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ActionViewSet(VersionedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for public Actions. See the api_docs/ for more info"""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.Action.objects.published()
    serializer_class_v1 = v1.ActionSerializer
    serializer_class_v2 = v2.ActionSerializer
    pagination_class = PublicViewSetPagination
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

        # WE Want to exclude values from this endpoint that the user has already
        # selected (if the user is authenticated AND we're hitting api v2)
        user = self.request.user
        if self.request.version == '2' and user.is_authenticated():
            chosen = user.useraction_set.values_list('action__id', flat=True)
            self.queryset = self.queryset.exclude(id__in=chosen)

        return self.queryset

    @detail_route(methods=['post'],
                  permission_classes=[IsContentAuthor],
                  url_path='order')
    def set_order(self, request, pk=None):
        """Allow certin users to update Actions through the api; but only
        to set the order.

            /api/actions/<id>/order/

        """
        try:
            # NOTE: we can't use self.get_object() here, because we're allowing
            # users to change items that may not yet be published.
            seq = int(request.data.get('sequence_order'))
            num = models.Action.objects.filter(pk=pk).update(sequence_order=seq)
            return Response(data={'updated': num}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                data={'error': "{0}".format(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


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
    pagination_class = PageSizePagination

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
        self.queryset = super().get_queryset().filter(user=self.request.user)

        # If we're trying to filter goals that are only relevant for
        # notifications (actions) delivered today, we need to first look
        # up those actions, then query for their parent behviors' goals.
        filter_on_today = bool(self.request.GET.get('today', False))

        if self.request.user.is_authenticated() and filter_on_today:
            today = local_day_range(self.request.user)
            useractions = models.UserAction.objects.filter(user=self.request.user)
            useractions = useractions.filter(
                Q(prev_trigger_date__range=today) |
                Q(next_trigger_date__range=today)
            )
            goal_ids = useractions.values_list(
                "action__behavior__goals__id", flat=True)
            self.queryset = self.queryset.filter(goal__id__in=goal_ids)

        # We may also filter this list of content by a goal id
        goal_filter = self.request.GET.get('goal', None)
        if goal_filter:
            self.queryset = self.queryset.filter(goal__id=goal_filter)

        return self.queryset

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
    pagination_class = PageSizePagination

    def get_queryset(self):
        # First, only expose content in Categories/Packages that are either
        # public or in which we've accepted the terms/consent form.
        self.queryset = super().get_queryset().filter(user=self.request.user)

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

    def create_parent_objects(self, request):
        """If the request includes all 3: category, goal, behavior, then
        let's try to get or create all of the user's objects at once.

        Returns a tuple containing a possibly modified request object, and a
        dict of parent object IDs, containing keys for `category` and `goal`.

        """
        # We'll *only* do this if we have all the necessary data.
        parents = {}
        checks = [
            'category' in request.data and bool(request.data['category']),
            'goal' in request.data and bool(request.data['goal']),
            'behavior' in request.data and bool(request.data['behavior']),
        ]
        if all(checks):
            # NOTE: request.data.pop returns a list, and we have to look up
            # each object individually in order to Create them.
            cat_id = pop_first(request.data, 'category')
            uc, _ = models.UserCategory.objects.get_or_create(
                user=request.user,
                category=models.Category.objects.filter(id=cat_id).first()
            )
            parents['category'] = cat_id

            goal_id = pop_first(request.data, 'goal')
            ug, _ = models.UserGoal.objects.get_or_create(
                user=request.user,
                goal=models.Goal.objects.filter(id=goal_id).first()
            )
            ug.primary_category = uc.category  # Set the primary goal.
            ug.save()
            parents['goal'] = goal_id
        return (request, parents)

    def create_child_objects(self, instance):
        try:
            instance.add_actions()
        except AttributeError:
            # If we added multiple behaviors, instance will be a list;
            for item in instance:
                item.add_actions()

    def create(self, request, *args, **kwargs):
        """Only create objects for the authenticated user."""
        if isinstance(request.data, list):
            # We're creating multiple items
            for d in request.data:
                d['user'] = request.user.id
        else:
            request.data['user'] = request.user.id

        # Call out to the superclass to create the UserBehavior for v1...
        if request.version == "1":
            return super().create(request, *args, **kwargs)

        # look for category, and goal objects then add them;
        # otherwise, this doesn't really do anything.
        request, parents = self.create_parent_objects(request)

        # The rest of this is pulled from DRFs mixins.CreateModelMixin, with
        # 1 change: We pass in parent object IDs to the serializer so it knows
        # if parent objets should be included in the response (for v2 of the api).
        serializer = self.get_serializer(data=request.data, parents=parents)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # As of v2 of the api, we also want to create UserActions for all
        # content within the selected behavior.
        # ... at this point the created UserBehavior is `serializer.instance`
        self.create_child_objects(serializer.instance)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

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
    pagination_class = PageSizePagination

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
        self.queryset = super().get_queryset().filter(user=self.request.user)

        # Now, filter on category, goal, behavior, action if necessary
        filter_on_today = bool(self.request.GET.get('today', False))
        category = self.request.GET.get('category', None)
        goal = self.request.GET.get('goal', None)
        behavior = self.request.GET.get('behavior', None)
        action = self.request.GET.get('action', None)

        if category is not None and category.isnumeric():
            self.queryset = self.queryset.filter(
                action__behavior__goals__categories__id=category)
        elif category is not None:
            self.queryset = self.queryset.filter(
                action__behavior__goals__categories__title_slug=category)

        if goal is not None and goal.isnumeric():
            self.queryset = self.queryset.filter(
                action__behavior__goals__id=goal)
        elif goal is not None:
            self.queryset = self.queryset.filter(
                action__behavior__goals__title_slug=goal)

        if behavior is not None and behavior.isnumeric():
            self.queryset = self.queryset.filter(action__behavior__id=behavior)
        elif behavior is not None:
            self.queryset = self.queryset.filter(
                action__behavior__title_slug=behavior)
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

        Returns a tuple containing a possibly modified request object, and a
        dict of parent object IDs, containing keys for `category`, `behavior`,
        and `goal`.

        """
        # We'll *only* do this if we have all the necessary data.
        parents = {}
        checks = [
            'category' in request.data and bool(request.data['category']),
            'goal' in request.data and bool(request.data['goal']),
            'behavior' in request.data and bool(request.data['behavior']),
            'action' in request.data and bool(request.data['action']),
        ]
        if all(checks):
            # NOTE: request.data.pop returns a list, and we have to look up
            # each object individually in order to Create them.
            cat_id = pop_first(request.data, 'category')
            uc, _ = models.UserCategory.objects.get_or_create(
                user=request.user,
                category=models.Category.objects.filter(id=cat_id).first()
            )
            parents['category'] = cat_id

            goal_id = pop_first(request.data, 'goal')
            ug, _ = models.UserGoal.objects.get_or_create(
                user=request.user,
                goal=models.Goal.objects.filter(id=goal_id).first()
            )
            ug.primary_category = uc.category  # Set the primary goal.
            ug.save()
            parents['goal'] = goal_id

            behavior_id = pop_first(request.data, 'behavior')
            ub, _ = models.UserBehavior.objects.get_or_create(
                user=request.user,
                behavior=models.Behavior.objects.filter(id=behavior_id).first()
            )
            parents['behavior'] = behavior_id

            # Also set the category & goal as primary
            request.data['primary_category'] = cat_id
            request.data['primary_goal'] = goal_id
        return (request, parents)

    def create(self, request, *args, **kwargs):
        """Only create objects for the authenticated user."""
        if isinstance(self.request.data, list):
            # We're creating multiple items
            for d in request.data:
                d['user'] = request.user.id
        else:
            # We're creating a single item
            request.data['user'] = request.user.id

        # Call out to the superclass to create the UserAction for v1...
        if request.version == "1":
            return super().create(request, *args, **kwargs)

        # look for action, category, behavior, goal objects, and add them;
        # otherwise, this doesn't really do anything.
        request, parents = self.create_parent_objects(request)

        # The rest of this is pulled from DRFs mixins.CreateModelMixin, with
        # 1 change: We pass in parent object IDs to the serializer so it knows
        # if parent objets should be included in the response (for v2 of the api).
        serializer = self.get_serializer(data=request.data, parents=parents)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def _toggle_custom_trigger(self, request, disabled):
        """Enables or Disables the custom trigger. NOTE: This *only* works
        on a custom trigger (not a default trigger). """
        if isinstance(disabled, list) and len(disabled) > 0:
            disabled = disabled[0]

        ua = self.get_object()
        request.data['user'] = ua.user.id
        request.data['action'] = ua.action.id
        try:
            # Attempt disabling the trigger
            ua.custom_trigger.disabled = bool(disabled)
            ua.custom_trigger.save()
        except AttributeError:
            pass  # This object didn't have a custom trigger
        return request

    def _include_trigger(self, request, trigger_rrule, trigger_time,
                         trigger_date, disabled=None):
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
        if disabled is not None and isinstance(disabled, list):
            disabled = disabled[0]

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
            'date': trigger_date,
            'disabled': bool(disabled)
        }
        trigger_serializer = v1.CustomTriggerSerializer(
            instance=trigger,
            data=trigger_data
        )

        # Create/Update the custom trigger object.
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
        """Allow setting/creating a custom trigger using the following
        information:

        * custom_trigger_rrule
        * custom_trigger_time
        * custom_trigger_date
        * custom_trigger_disabled (optional)

        """
        disabled = request.data.pop('custom_trigger_disabled', None)

        # Update the custom trigger date/time/recurrence
        if self._has_custom_trigger_params(request.data.keys()):
            request = self._include_trigger(
                request,
                trigger_rrule=request.data.pop("custom_trigger_rrule", None),
                trigger_time=request.data.pop("custom_trigger_time", None),
                trigger_date=request.data.pop("custom_trigger_date", None),
                disabled=disabled
            )
        elif disabled is not None:
            # Enable/Disable the custom trigger
            request = self._toggle_custom_trigger(request, disabled)

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
    permission_classes = [IsOwner]
    pagination_class = PageSizePagination

    def get_queryset(self):
        self.queryset = super().get_queryset().filter(user=self.request.user)

        # We may also filter this list of content by a category id
        category = self.request.GET.get('category', None)
        if category:
            self.queryset = self.queryset.filter(category__id=category)

        return self.queryset

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
    pagination_class = PageSizePagination

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
    from [Goals](/api/goals/) and [Actions](/api/actions/). While we index
    content from both types of objects, this endpoint currently only returns
    serialized `Goal` instances.

    ## Searching

    To search this content, send a GET request with a `q` parameter
    containing your search terms. For example:

        {'q': 'wellness'}

    A GET request without a search term will return all Goals.

    ## Results

    A paginated list of results will be returned, and each result will contain
    the following attributes:

    * `id`: The ID of the object represented
    * `object_type`: A lowercase string representing the type of object
      (currently this will always be `search-goal`)
    * `title`: The title of the object.
    * `description`: The full description of the object.
    * `updated_on`: The date/time on which the object was last updated.
    * `text`: The full text stored in the search index. This is the content
      against which search is performed.
    * `highlighted`: A string containing html-highlighted matches. The
      highlighted keywords are wrapped with `<em>` tags.
    * In addition, there will be a nested serialized object, in the case of
      goals, this will called `goal`.

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
    pagination_class = PageSizePagination

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
    pagination_class = PageSizePagination

    def get_queryset(self):
        self.queryset = models.CustomAction.objects.filter(user=self.request.user)

        # Filter on CustomGoals
        cg = self.request.GET.get('customgoal', None)
        if cg and cg.isnumeric():
            self.queryset = self.queryset.filter(customgoal__id=cg)
        elif cg:
            self.queryset = self.queryset.filter(customgoal__title_slug=cg)

        return self.queryset

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

        # XXX: to allow us to update *only* the trigger details, we need to
        # add the title, customgoal, notification_text back in (since the
        # superclass requires these).
        if 'title' not in request.data:
            request.data['title'] = customaction.title
        if 'customgoal' not in request.data and customaction.customgoal_id:
            request.data['customgoal'] = customaction.customgoal_id
        elif customaction.customgoal:
            request.data['customgoal'] = customaction.customgoal.id
        if 'notification_text' not in request.data:
            request.data['notification_text'] = customaction.notification_text
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


class DailyProgressViewSet(VersionedViewSetMixin,
                           mixins.CreateModelMixin,
                           mixins.ListModelMixin,
                           mixins.RetrieveModelMixin,
                           mixins.UpdateModelMixin,
                           viewsets.GenericViewSet):
    """ViewSet for DailyProgress. See the api_docs/ for more info"""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.DailyProgress.objects.all()
    serializer_class_v1 = v1.DailyProgressSerializer
    serializer_class_v2 = v2.DailyProgressSerializer
    docstring_prefix = "goals/api_docs"
    permission_classes = [IsOwner]
    pagination_class = PageSizePagination

    def get_queryset(self):
        if not self.request.user.is_authenticated():
            return self.queryset.none()
        qs = super().get_queryset()
        return qs.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        """Ensure our user id gets set correctly."""
        request.data['user'] = request.user.id
        return super().update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        # Ensure we don't create duplicates for a day. If the thing exists
        # for today, fetch it an update instead.
        obj_id = models.DailyProgress.objects.exists_today(request.user)
        if obj_id:
            request.data['id'] = obj_id
            kwargs['pk'] = obj_id  # XXX: We can't just set this in kwargs...
            self.kwargs = kwargs  # XXX: we have to also save it on the class
            return self.update(request, *args, **kwargs)
        return super().create(request, *args, **kwargs)

    @list_route(methods=['post'], permission_classes=[IsOwner], url_path='checkin')
    def set_progress(self, request, pk=None):
        """A route that allows us to set daily checkin values related to
        a user's goal(s). (the end-of-the-day checkin in the app).

        Expected Data:

            {
              "goal": <goal_id>
              "daily_checkin": <number>
            }

        This endpoint, which only accepts POST requests is available at:

            /api/users/progress/checkin/

        """
        err_msg = ""
        if not self.request.user.is_authenticated():
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            # Ensure the data we're getting is valid
            value = int(request.data.get('daily_checkin', None))
            goal_id = request.data.get('goal', None)
            assert request.user.usergoal_set.filter(goal__id=goal_id).exists()

            dp = models.DailyProgress.objects.for_today(request.user)
            dp.set_goal_status(goal_id, value)
            dp.save()
            serializer = self.get_serializer(dp)
            return Response(serializer.data)
        except (ValueError, TypeError):
            err_msg = "Invalid value: {}".format(request.data.get('daily_checkin'))
        except AssertionError:
            err_msg = "User has no goal with id: {}".format(request.data.get('goal'))

        return Response(data={'error': err_msg}, status=status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------------------------------
    # TODO: Allow users to view their bucket for a bheavior and to manually set
    # their bucket/status (DailyProgress.set_status)
    # -------------------------------------------------------------------------
    @list_route(methods=['get', 'post'], permission_classes=[IsOwner], url_path='behaviors')
    def behavior_status(self, request, pk=None):
        """Set or list the status of your behaviors (i.e. their current bucket)
        based on the latest DailyProgress data.

        Endpoint: [/api/users/progress/behaviors/](/api/users/progress/behaviors/)

        GET requests return data of the form:

            {
                'behavior-<id>': <bucket-name>
            }

        A successful POST request will return the same data, but expects a
        payload of the form:

            {
                'behavior':<id>
                'bucket': <bucket-name>
            }

        Bucket names must be one of: `prep`, `core`, `helper`, `checkup`.

        """
        results = {}
        if not self.request.user.is_authenticated():
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            dp = models.DailyProgress.objects.filter(user=request.user).latest()

            # POST request: update the bucket and THEN show the list
            if request.method == "POST":
                bid = request.data.get('behavior', None)
                bucket_name = request.data.get('bucket', None)
                assert bucket_name in models.Action.BUCKET_ORDER
                ub = request.user.userbehavior_set.get(behavior__id=bid)
                dp.set_status(ub.behavior, bucket_name)
                dp.save()

            # GET requests: show a list of behavior / bucket info?
            # Posts return the same data.
            results = dp.behaviors_status

        except (models.UserBehavior.DoesNotExist, AssertionError) as e:
            err_msg = "{}".format(e)  # NOTE: AssertionError has not message.
            data = {'error': err_msg or "Invalid bucket name"}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        except models.DailyProgress.DoesNotExist:
            pass

        return Response(data=results, status=status.HTTP_200_OK)
