from calendar import Calendar
from collections import defaultdict, Counter, OrderedDict
from datetime import datetime, timedelta
from hashlib import md5
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Count, Max, Q, Sum
from django.db.models.functions import Length
from django.http import (
    HttpResponse, HttpResponseBadRequest, HttpResponseForbidden,
    HttpResponseNotFound, JsonResponse
)
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import timesince
from django.template.loader import render_to_string
from django.views.generic import DetailView, FormView, ListView, TemplateView, View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.utils import timezone
from django.utils.text import slugify

from django_fsm import TransitionNotAllowed
from django_rq import job
from notifications import queue
from userprofile.forms import UserForm
from userprofile.models import UserProfile
from utils.db import get_max_order
from utils.forms import EmailForm, SetNewPasswordForm
from utils.dateutils import dates_range
from utils.user_utils import local_day_range, local_now, to_localtime

from . import user_feed
from . email import send_package_cta_email, send_package_enrollment_batch
from . forms import (
    ActionForm,
    ActionPriorityForm,
    AcceptEnrollmentForm,
    ActionTriggerForm,
    BehaviorForm,
    CategoryForm,
    ContentAuthorForm,
    CTAEmailForm,
    DisableTriggerForm,
    EnrollmentReminderForm,
    GoalForm,
    OrganizationForm,
    PackageEnrollmentForm,
    ProgramForm,
    TitlePrefixForm,
    TriggerForm,
    UploadImageForm,
)
from . mixins import (
    ContentAuthorMixin, ContentEditorMixin, ContentViewerMixin,
    PackageManagerMixin, ReviewableUpdateMixin, StateFilterMixin,
    StaffRequiredMixin,
)
from . models import (
    Action,
    Behavior,
    Category,
    DailyProgress,
    Goal,
    Organization,
    PackageEnrollment,
    Program,
    Trigger,
    UserCompletedAction,
    UserGoal,
    popular_actions,
    popular_behaviors,
    popular_goals,
    popular_categories,
)
from . permissions import (
    ContentPermissions,
    is_content_editor,
    is_contributor,
    permission_required,
    staff_required,
    superuser_required,
)
from . sequence import get_next_useractions_in_sequence, get_next_in_sequence_data
from . utils import num_user_selections


logger = logging.getLogger(__name__)


class BaseTransferView(FormView):
    """A base view that should be subclassed for models where we want to enable
    transferring "ownership". The model must have some FK field to a User, and
    be written in a way that assumes that user is the owner.

    To use this, you must define the following:

    * model: The Model class
    * pk_field: The Primary Key field name (typically "pk" or "id")
    * owner_field: The name of the FK to User. (e.g. "user" or "created_by")

    This class also assumes that existing users, superusers, and staff users
    have the ability to transfer owndership.

    """
    # Custom attributes
    model = None
    pk_field = None
    owner_field = None

    # FormView attributes
    form_class = ContentAuthorForm
    http_method_names = ['get', 'post']
    template_name = "goals/transfer.html"

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['object'] = self.object
        ctx['owner'] = getattr(self.object, self.owner_field)
        return ctx

    def get_object(self, kwargs):
        if None in [self.model, self.pk_field, self.owner_field]:
            raise RuntimeError(
                "BaseTransferView subclasses must define the following: "
                "model, pk_field, and owner_field."
            )
        params = {self.pk_field: kwargs.get(self.pk_field, None)}
        return get_object_or_404(self.model, **params)

    def _can_transfer(self, user):
        return any([
            getattr(self.object, self.owner_field) == user,
            user.is_staff,
            user.is_superuser,
        ])

    def _http_method(self, request, *args, **kwargs):
        if not self._can_transfer(request.user):
            messages.warning(request, "You are not the owner of that object.")
            return redirect(self.object.get_absolute_url())
        elif request.method == "GET":
            return super().get(request, *args, **kwargs)
        elif request.method == "POST":
            return super().post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(kwargs)
        return self._http_method(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object(kwargs)
        return self._http_method(request, *args, **kwargs)

    def form_valid(self, form):
        # Set the new owner and carry on.
        setattr(self.object, self.owner_field, form.cleaned_data['user'])
        self.object.save()
        return super().form_valid(form)


class PublishView(View):
    """A Simple Base View for subclasses that need to publish content. This
    is overridden by views that specify the model and slug_field for different
    types of content.

    """
    http_method_names = ['post']
    model = None
    slug_field = None

    def get_object(self, kwargs):
        if self.model is None or self.slug_field is None:
            raise RuntimeError(
                "PublishView subclasses must define a model and slug_field "
                "attributes."
            )
        params = {self.slug_field: kwargs.get(self.slug_field, None)}
        return self.model.objects.get(**params)

    def post(self, request, *args, **kwargs):
        try:
            obj = self.get_object(kwargs)
            selections = num_user_selections(obj)
            confirmed = request.POST.get('confirmed', False) or selections <= 0
            is_superuser = request.user.is_superuser

            if request.POST.get('publish', False):
                obj.publish()
                obj.save(updated_by=request.user)
                messages.success(request, "{0} has been published".format(obj))
            elif request.POST.get('decline', False):
                obj.decline()
                obj.save(updated_by=request.user)
                messages.success(request, "{0} has been declined".format(obj))
            elif confirmed and request.POST.get('draft', False):
                obj.draft()
                obj.save(updated_by=request.user)
                messages.success(request, "{0} is now in Draft".format(obj))
            elif request.POST.get('draft', False) and selections > 0:
                context = {'selections': selections, 'object': obj}
                return render(request, 'goals/confirm_state_change.html', context)
            elif is_superuser and request.POST.get('publish_children', False):
                count = 0   # count *all* children published.
                if not obj.state == "published":
                    obj.publish()
                    obj.save(updated_by=request.user)
                    count += 1

                # Now, publish all the children
                children = obj.publish_children(updated_by=request.user)
                count += len(children)

                # and the children's children
                while len(children) > 0:
                    children = [
                        item.publish_children(updated_by=request.user)
                        for item in children
                    ]
                    children = [val for sublist in children for val in sublist]
                    count += len(children)
                messages.success(request, "Published {} items".format(count))
            return redirect(obj.get_absolute_url())

        except self.model.DoesNotExist:
            messages.error(
                request, "Could not find the specified {0}".format(self.model)
            )
        except TransitionNotAllowed:
            messages.error(request, "Unable to process transition.")
        return redirect("goals:index")


class ContentDeleteView(DeleteView):
    """This is a Base DeleteView for our Content models.It doesn't allow for
    deletion if users have selected the object (e.g. Content or Goal).

    Works with: Category, Goal, Behavior, Action

    """
    def get_num_user_selections(self):
        if not hasattr(self, "_num_user_selections"):
            obj = self.get_object()
            self._num_user_selections = num_user_selections(obj)
        return self._num_user_selections

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_user_selections'] = self.get_num_user_selections()
        return context

    def delete(self, request, *args, **kwargs):
        if self.get_num_user_selections() > 0:
            msg = "You cannot remove objects that have been selected by users"
            return HttpResponseForbidden(msg)
        return super().delete(request, *args, **kwargs)


class CreatedByView(CreateView):
    """A Subclass of CreateView that tracks who created the object."""

    def form_valid(self, form):
        result = super(CreatedByView, self).form_valid(form)
        self.object.save(created_by=self.request.user)
        return result


class IndexView(ContentViewerMixin, TemplateView):
    template_name = "goals/index.html"

    def get(self, request, *args, **kwargs):
        """Include the following additional info for the goal app's index:

        * pending and declined content items for editors
        * all "my" information (for authors)
        * some stats on the most popular content.

        """
        # Only the fields needed for Category, Goal, Behavior, Action objects
        # on this page.
        only_fields = [
            'id', 'title', 'title_slug', 'updated_on', 'updated_by',
            'created_by', 'state',
        ]
        context = self.get_context_data(**kwargs)
        is_contributor = request.user.category_contributions.exists()
        if is_content_editor(request.user) or is_contributor:
            context['is_editor'] = True

            # Show content pending review.
            mapping = {
                'categories': Category.objects.only(*only_fields).filter,
                'goals': Goal.objects.only(*only_fields).filter,
                'behaviors': Behavior.objects.only(*only_fields).filter,
                'actions': Action.objects.only(*only_fields).filter,
            }
            for key, func in mapping.items():
                qs = func(state='pending-review').order_by("-updated_on")
                if is_contributor:
                    qs = qs.for_contributor(request.user)
                context[key] = qs

        # List content created/updated by the current user.
        conditions = Q(created_by=request.user) | Q(updated_by=request.user)
        mapping = {
            'my_categories': Category.objects.filter,
            'my_goals': Goal.objects.only(*only_fields).filter,
            'my_behaviors': Behavior.objects.only(*only_fields).filter,
            'my_actions': Action.objects.only(*only_fields).filter,
        }
        for key, func in mapping.items():
            context[key] = func(conditions)

        # Evaluate to see if the curent user has any content available
        total_items = sum([
            context['my_categories'].count(),
            context['my_goals'].count(),
            context['my_behaviors'].count(),
            context['my_actions'].count(),
        ])
        context['has_my_content'] = total_items > 0
        context['total_my_content'] = total_items

        # IF the result is too big, limit the results...
        if total_items > 40:
            for key, func in mapping.items():
                context[key] = context[key][0:10]
        context['num_my_content'] = sum(
            len(context[key]) for key in mapping.keys()
        )
        return self.render_to_response(context)


class MyContentView(ContentViewerMixin, TemplateView):
    """A list of all content 'owned' by the authenticated users.
    This information is abbreviated in the IndexView, but if the user has
    a lot of content this view lets them see it all at once.
    """
    template_name = "goals/my_content.html"

    def get(self, request, *args, **kwargs):
        """Includes all content "owned" by the authenticated users into
        the context; e.g. the author's "my content"

        """
        context = self.get_context_data(**kwargs)

        # Only the fields needed for Category, Goal, Behavior, Action objects
        # on this page.
        only_fields = [
            'id', 'title', 'title_slug', 'updated_on', 'updated_by',
            'created_by', 'state',
        ]
        # List content created/updated by the current user.
        conditions = Q(created_by=request.user) | Q(updated_by=request.user)
        mapping = {
            'my_categories': Category.objects.filter,
            'my_goals': Goal.objects.only(*only_fields).filter,
            'my_behaviors': Behavior.objects.only(*only_fields).filter,
            'my_actions': Action.objects.only(*only_fields).filter,
        }
        for key, func in mapping.items():
            context[key] = func(conditions)

        total_items = sum([
            context['my_categories'].count(),
            context['my_goals'].count(),
            context['my_behaviors'].count(),
            context['my_actions'].count(),
        ])
        context['has_my_content'] = total_items > 0
        context['total_my_content'] = total_items
        context['num_my_content'] = total_items
        return self.render_to_response(context)


class CategoryListView(ContentViewerMixin, StateFilterMixin, ListView):
    model = Category
    context_object_name = 'categories'
    template_name = "goals/category_list.html"

    def _filters(self):
        kw = {}

        selected = self.request.GET.get('selected_by_default', None)
        if selected is not None:
            kw['selected_by_default'] = bool(selected)

        featured = self.request.GET.get('featured', None)
        if featured is not None:
            kw['grouping__gte'] = 0

        packaged = self.request.GET.get('packaged_content', None)
        if packaged is not None:
            kw['packaged_content'] = bool(packaged)

        organizations = self.request.GET.get('organizations', None)
        if organizations is not None:
            kw['organizations__isnull'] = False
        return kw

    def get_queryset(self):
        queryset = super().get_queryset().filter(**self._filters())
        queryset = queryset.annotate(Count('usercategory'))
        return queryset.prefetch_related(
            "goal_set", "behavior_set", "organizations", "program_set")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self._filters())
        if context.get('grouping__gte', None) == 0:
            context['featured'] = True
        if context.get('organizations__isnull') is False:
            context['organizations'] = True
        context['category_list'] = True
        return context


class CategoryDetailView(ContentViewerMixin, DetailView):
    queryset = Category.objects.all()
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = context['object']

        result = category.goals.aggregate(Max('sequence_order'))
        result = result.get('sequence_order__max') or 0
        context['order_values'] = list(range(result + 5))
        return context


class CategoryCreateView(ContentEditorMixin, CreatedByView):
    model = Category
    form_class = CategoryForm
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"

    def get_form_kwargs(self):
        """Includes the current user in the form's kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        url = super().get_success_url()
        messages.success(self.request, "Your category has been created.")
        return url

    def get_initial(self, *args, **kwargs):
        """Pre-populate the value for the initial order. This can't be done
        at the class level because we want to query the value each time."""
        initial = super(CategoryCreateView, self).get_initial(*args, **kwargs)
        if 'order' not in initial:
            initial['order'] = get_max_order(Category)
        return initial


class CategoryDuplicateView(CategoryCreateView):
    """Initializes the Create form with a copy of data from another object."""
    def get_initial(self, *args, **kwargs):
        initial = super(CategoryDuplicateView, self).get_initial(*args, **kwargs)
        try:
            obj = self.get_object()
            initial.update({
                "title": "Copy of {0}".format(obj.title),
                "description": obj.description,
                "color": obj.color,
            })
        except self.model.DoesNotExist:
            pass
        initial['order'] = get_max_order(Category)
        return initial


class CategoryPublishView(ContentEditorMixin, PublishView):
    model = Category
    slug_field = 'title_slug'


class CategoryTransferView(BaseTransferView):
    model = Category
    pk_field = "pk"
    owner_field = "created_by"
    success_url = reverse_lazy('goals:category-list')


class CategoryUpdateView(ContentEditorMixin, ReviewableUpdateMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"

    def get_form_kwargs(self):
        """Includes the current user in the form's kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        url = super().get_success_url()
        messages.success(self.request, "Your category has been saved")
        return url


class CategoryDeleteView(ContentEditorMixin, ContentDeleteView):
    model = Category
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"
    success_url = reverse_lazy('goals:index')


@user_passes_test(superuser_required, login_url='/goals/')
def reset_default_triggers_in_category(request, pk, title_slug):
    """This is a util view that lets a superuser do one of the following:

    1. Reset all default triggers (time of day/ frequency) for all Actions
       within a category, OR
    2. Reset all Action priorities within the category.

    XXX: this is probably too much for one view, but it's convenient to put
         both options, here.

    """
    category = get_object_or_404(Category, pk=pk, title_slug=title_slug)

    if request.method == "POST":
        trigger_form = TriggerForm(request.POST, prefix="triggers")
        reset_triggers = trigger_form.is_valid()

        priority_form = ActionPriorityForm(request.POST, prefix="priority")
        reset_priorities = priority_form.is_valid()

        if any([reset_triggers, reset_priorities]):
            trigger_count = 0
            priority_count = 0
            for action in category.actions:
                # ToD and Frequency are optional, so only do updates if
                # they've been selected for changes.
                tod = trigger_form.cleaned_data.get('time_of_day')
                freq = trigger_form.cleaned_data.get('frequency')
                if reset_triggers and (tod or freq):
                    action.default_trigger.reset()
                    if tod:
                        action.default_trigger.time_of_day = tod
                    if freq:
                        action.default_trigger.frequency = freq
                    action.default_trigger.save()
                    trigger_count += 1

                # Priority is also optional.
                priority = priority_form.cleaned_data.get('priority')
                if reset_priorities and priority:
                    action.priority = priority
                    action.save()
                    priority_count += 1

            msg = "Reset {} default triggers and {} priorities.".format(
                trigger_count,
                priority_count
            )
            messages.success(request, msg)
            return redirect(category.get_absolute_url())
    else:
        trigger_form = TriggerForm(prefix="triggers")
        priority_form = ActionPriorityForm(prefix="priority")

    template = "goals/reset_default_triggers_in_category.html"
    ctx = {
        'trigger_form': trigger_form,
        'priority_form': priority_form,
        'category': category,
    }
    return render(request, template, ctx)


class GoalListView(ContentViewerMixin, StateFilterMixin, ListView):
    model = Goal
    context_object_name = 'goals'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(Count('usergoal'))
        if self.request.GET.get('category', False):
            queryset = queryset.filter(categories__pk=self.request.GET['category'])
        return queryset.prefetch_related("behavior_set", "categories")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_id = self.request.GET.get('category', None)
        if category_id:
            context['category'] = Category.objects.get(pk=category_id)
        return context


class GoalDetailView(ContentViewerMixin, DetailView):
    queryset = Goal.objects.all()
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        goal = context['object']

        # IDs for this Goal's child behaviors
        bids = goal.behavior_set.values_list('pk', flat=True)
        order_values = Behavior.objects.filter(pk__in=bids).aggregate(
            Max('sequence_order')
        )
        order_values = order_values.get('sequence_order__max') or 0

        # include values for the Action's sequence_orders
        result = Action.objects.filter(behavior__id__in=bids).aggregate(
            Max('sequence_order')
        )

        # Pick the larger order value from Behaviors and Actions
        result = max(order_values, result.get('sequence_order__max') or 0)
        context['order_values'] = list(range(result + 5))
        return context


class GoalCreateView(ContentAuthorMixin, CreatedByView):
    model = Goal
    form_class = GoalForm
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"

    def get_initial(self):
        data = self.initial.copy()
        data['categories'] = self.request.GET.getlist('category', None)
        return data

    def get_success_url(self):
        url = super().get_success_url()
        messages.success(self.request, "Your goal has been created.")
        return url

    def form_valid(self, form):
        """Upons saving, also check if this was submitted for review."""
        result = super().form_valid(form)
        if self.request.POST.get('review', False):
            msg = ("This goal must have child behaviors that are either "
                   "published or in review before it can be reviewed.")
            messages.warning(self.request, msg)

        # Save the user that created/upadted this object.
        goal = self.object
        goal.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )

        # If we've duplicated a Goal, look up the original's id and
        # duplicate all of it's Behaviors & Actions.
        # NOTE: This will be slow and inefficient.
        original = form.cleaned_data.get('original_goal', None)

        if original:
            prefix = md5(timezone.now().strftime("%c").encode('utf8')).hexdigest()[:6]
            original_goal = Goal.objects.get(pk=original)

            for old_behavior in original_goal.behavior_set.all():
                title = "({}) Copy of {}".format(prefix, old_behavior.title)
                note = "Created when duplicating Goal {}: {}".format(
                    goal.id, goal.title)
                params = {
                    "title": title,
                    "sequence_order": old_behavior.sequence_order,
                    "description": old_behavior.description,
                    "more_info": old_behavior.more_info,
                    "informal_list": old_behavior.informal_list,
                    "external_resource": old_behavior.external_resource,
                    "source_link": old_behavior.source_link,
                    "source_notes": old_behavior.source_notes,
                    "notes": note,
                }
                new_behavior = Behavior.objects.create(**params)
                new_behavior.goals.add(goal)
                new_behavior.save()

                duplicate_actions = []
                for action in old_behavior.action_set.all():
                    title = "({}) Copy of {}".format(prefix, action.title)
                    params = {
                        "title": title,
                        "title_slug": slugify(title),
                        "sequence_order": action.sequence_order,
                        "behavior": new_behavior,
                        "description": action.description,
                        "more_info": action.more_info,
                        "notification_text": action.notification_text,
                        "external_resource": action.external_resource,
                        "external_resource_name": action.external_resource_name,
                        "priority": action.priority,
                        "bucket": action.bucket,
                        "notes": note,
                    }
                    duplicate_actions.append(Action(**params))
                Action.objects.bulk_create(duplicate_actions)
        return result


class GoalDuplicateView(GoalCreateView):
    """Initializes the Create form with a copy of data from another object."""
    def get_initial(self, *args, **kwargs):
        initial = super(GoalDuplicateView, self).get_initial(*args, **kwargs)
        try:
            obj = self.get_object()
            initial.update({
                "title": "Copy of {0}".format(obj.title),
                'sequence_order': obj.sequence_order,
                "categories": obj.categories.values_list("id", flat=True),
                "description": obj.description,
                "original_goal": obj.id,
            })
        except self.model.DoesNotExist:
            pass
        return initial


class GoalPublishView(ContentEditorMixin, PublishView):
    model = Goal
    slug_field = 'title_slug'


class GoalTransferView(BaseTransferView):
    model = Goal
    pk_field = "pk"
    owner_field = "created_by"


class GoalUpdateView(ContentAuthorMixin, ReviewableUpdateMixin, UpdateView):
    model = Goal
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"
    form_class = GoalForm

    def get_context_data(self, **kwargs):
        context = super(GoalUpdateView, self).get_context_data(**kwargs)
        context['goals'] = Goal.objects.all().prefetch_related(
            "categories",
            "behavior_set"
        )
        return context


class GoalDeleteView(ContentEditorMixin, ContentDeleteView):
    model = Goal
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"
    success_url = reverse_lazy('goals:index')


class TriggerListView(ContentViewerMixin, ListView):
    model = Trigger
    fields = (
        'id', 'name', 'time', 'trigger_date', 'recurrences',
        'relative_value', 'relative_units',
        'time_of_day', 'frequency', 'action_default',
    )
    queryset = Trigger.objects.default().values(*fields)
    context_object_name = 'triggers'


class TriggerDetailView(ContentEditorMixin, DetailView):
    queryset = Trigger.objects.default()
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"


class BehaviorListView(ContentViewerMixin, StateFilterMixin, ListView):
    model = Behavior
    context_object_name = 'behaviors'
    paginate_by = 200

    def get_queryset(self):
        queryset = super().get_queryset().only(
            'id', 'state', 'icon', 'sequence_order', 'title', 'title_slug',
            'description', 'informal_list'
        )
        if self.request.GET.get('goal', False):
            queryset = queryset.filter(goals__pk=self.request.GET['goal'])
        queryset = queryset.annotate(Count('userbehavior'))
        return queryset.order_by('-updated_on')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        goal_id = self.request.GET.get('goal', None)
        if goal_id:
            context['goal'] = Goal.objects.get(pk=goal_id)
        return context


class BehaviorDetailView(ContentViewerMixin, DetailView):
    queryset = Behavior.objects.all()
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        behavior = context['object']

        # XXX: Disabling bucket-related stuff
        # Determine if this Behavior contains dynamic notifications
        # obj = context['object']
        # qs = Behavior.objects.contains_dynamic().filter(pk=obj.id)
        # context['contains_dynamic'] = qs.exists()
        # context['action_url'] = Action.get_create_reinforcing_action_url()

        # include values for the Action's sequence_orders
        result = behavior.action_set.aggregate(Max('sequence_order'))
        result = result.get('sequence_order__max') or 0
        context['order_values'] = list(range(result + 5))
        return context


class BehaviorCreateView(ContentAuthorMixin, CreatedByView):
    model = Behavior
    form_class = BehaviorForm
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"

    def get_initial(self):
        data = self.initial.copy()
        data['goals'] = self.request.GET.getlist('goal', None)
        return data

    def form_valid(self, form):
        """Submitting for review on creation should to the appropriate state
        transition. """
        result = super().form_valid(form)
        if self.request.POST.get('review', False):
            self.object.review()  # Transition to the new state
            msg = "{0} has been submitted for review".format(self.object)
            messages.success(self.request, msg)
        else:
            messages.success(self.request, "Your behavior has been created.")

        self.object.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )

        # If we've duplicated a behavior, look up the original's id and
        # duplicate all of it's Actions
        original = form.cleaned_data.get('original_behavior', None)
        if original:
            original = Behavior.objects.get(pk=original)
            duplicate_actions = []
            for action in original.action_set.all():
                note = "Created when duplicating Behavior {}: {}".format(
                    self.object.id, self.object.title)
                params = {
                    "title": "Copy of {0}".format(action.title),
                    "title_slug": slugify("Copy of {0}".format(action.title)),
                    "sequence_order": action.sequence_order,
                    "behavior": self.object,
                    "description": action.description,
                    "more_info": action.more_info,
                    "notification_text": action.notification_text,
                    "external_resource": action.external_resource,
                    "external_resource_name": action.external_resource_name,
                    "priority": action.priority,
                    "bucket": action.bucket,
                    "notes": note,
                }
                duplicate_actions.append(Action(**params))
            Action.objects.bulk_create(duplicate_actions)
        return result


class BehaviorDuplicateView(BehaviorCreateView):
    """Initializes the Create form with a copy of data from another object.

    NOTE: This view simply populates the BehaviorForm's initial data; creating
    the new behavior is handled by BehaviorCreateView.

    """
    def get_initial(self, *args, **kwargs):
        initial = super(BehaviorDuplicateView, self).get_initial(*args, **kwargs)
        try:
            obj = self.get_object()
            title = "({}) Copy of {}".format(
                md5(timezone.now().strftime("%c").encode('utf8')).hexdigest()[:6],
                obj.title
            )
            initial.update({
                "title": title,
                "sequence_order": obj.sequence_order,
                "description": obj.description,
                "more_info": obj.more_info,
                "informal_list": obj.informal_list,
                "external_resource": obj.external_resource,
                "goals": obj.goals.values_list("id", flat=True),
                "source_link": obj.source_link,
                "source_notes": obj.source_notes,
                "original_behavior": obj.id,
            })
        except self.model.DoesNotExist:
            pass
        return initial


class BehaviorPublishView(ContentEditorMixin, PublishView):
    model = Behavior
    slug_field = 'title_slug'


class BehaviorTransferView(BaseTransferView):
    model = Behavior
    pk_field = "pk"
    owner_field = "created_by"


class BehaviorUpdateView(ContentAuthorMixin, ReviewableUpdateMixin, UpdateView):
    model = Behavior
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"
    form_class = BehaviorForm

    def get_context_data(self, **kwargs):
        context = super(BehaviorUpdateView, self).get_context_data(**kwargs)
        context['behaviors'] = Behavior.objects.all()
        return context


class BehaviorDeleteView(ContentEditorMixin, ContentDeleteView):
    model = Behavior
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"
    success_url = reverse_lazy('goals:index')


class ActionListView(ContentViewerMixin, StateFilterMixin, ListView):
    model = Action
    context_object_name = 'actions'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(Count('useraction'))
        if self.request.GET.get('behavior', False):
            queryset = queryset.filter(behavior__id=self.request.GET['behavior'])
        return queryset.select_related("behavior__title").order_by('-updated_on')

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        behavior_id = self.request.GET.get('behavior', None)
        if behavior_id:
            ctx['behavior'] = Behavior.objects.get(pk=behavior_id)
        return ctx


class ActionDetailView(ContentViewerMixin, DetailView):
    queryset = Action.objects.all()
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"
    pk_url_kwarg = 'pk'

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx['disable_trigger_form'] = DisableTriggerForm()
        return ctx


class ActionCreateView(ContentAuthorMixin, CreatedByView):
    model = Action
    form_class = ActionForm
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"
    pk_url_kwarg = 'pk'
    action_type = Action.SHOWING
    action_type_name = 'Showing'
    trigger_date = None

    def _set_action_type(self, action_type):
        """Ensure the provided action type is valid."""
        if action_type in [at[0] for at in Action.ACTION_TYPE_CHOICES]:
            self.action_type = action_type
            self.action_type_name = [
                at[1] for at in Action.ACTION_TYPE_CHOICES
                if action_type == at[0]
            ][0]

    def _set_trigger_date(self, date):
        if date:
            self.trigger_date = datetime.strptime(date, "%Y-%m-%d")

    def get_initial(self):
        data = self.initial.copy()
        data.update(self.form_class.INITIAL[self.action_type])
        data['behavior'] = self.request.GET.get('behavior', None)
        return data

    def get(self, request, *args, **kwargs):
        # See if we're creating a specific Action type, and if so,
        # prepopulate the form with some initial data.
        self._set_action_type(request.GET.get("actiontype", self.action_type))
        self._set_trigger_date(request.GET.get("date", None))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Handle dealing with 2 forms.
        self.object = None
        form = self.get_form()
        trigger_form = ActionTriggerForm(request.POST, prefix="trigger")
        if form.is_valid() and trigger_form.is_valid():
            return self.form_valid(form, trigger_form)
        else:
            return self.form_invalid(form, trigger_form)

    def get_form(self, form_class=None):
        """Include the user as a keyword arg for the form class."""
        form_class = form_class or self.get_form_class()
        kwargs = self.get_form_kwargs()
        kwargs['user'] = self.request.user
        return form_class(**kwargs)

    def form_valid(self, form, trigger_form):
        self.object = form.save()
        default_trigger = trigger_form.save(commit=False)
        trigger_name = "Default: {0}-{1}".format(self.object, self.object.id)
        default_trigger.name = trigger_name[:128]
        default_trigger.save()
        self.object.default_trigger = default_trigger

        # If the POSTed data contains a True 'review' value, the user clicked
        # the "Submit for Review" button.
        if self.request.POST.get('review', False):
            self.object.review()  # Transition to the new state
            msg = "{0} has been submitted for review".format(self.object)
            messages.success(self.request, msg)
        else:
            messages.success(self.request, "Your notification has been created.")
        self.object.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
        return redirect(self.get_success_url())

    def form_invalid(self, form, trigger_form):
        ctx = self.get_context_data(form=form, trigger_form=trigger_form)
        return self.render_to_response(ctx)

    def get_context_data(self, **kwargs):
        context = super(ActionCreateView, self).get_context_data(**kwargs)
        context['Action'] = self.model
        context['action_type'] = self.action_type
        context['action_type_name'] = self.action_type_name

        # We also list all existing actions & link to them.
        context['actions'] = Action.objects.all().select_related("behavior__title")

        # pre-populate some dynamic content displayed to the user regarding
        # an action's parent behavior.
        context['behaviors'] = Behavior.objects.values(
            "id", "description", "informal_list"
        )
        if 'trigger_form' not in context and self.trigger_date:
            context['trigger_form'] = ActionTriggerForm(
                prefix="trigger",
                initial={'trigger_date': self.trigger_date.strftime("%m/%d/%Y")}
            )
        elif 'trigger_form' not in context:
            context['trigger_form'] = ActionTriggerForm(prefix="trigger")
        return context


class ActionDuplicateView(ActionCreateView):
    """Initializes the Create form with a copy of data from another object."""
    def get_initial(self, *args, **kwargs):
        initial = super(ActionDuplicateView, self).get_initial(*args, **kwargs)
        try:
            obj = self.get_object()
            initial.update({
                "title": "Copy of {0}".format(obj.title),
                "sequence_order": obj.sequence_order,
                "behavior": obj.behavior.id,
                "description": obj.description,
                "more_info": obj.more_info,
                "notification_text": obj.notification_text,
                "external_resource": obj.external_resource,
                "external_resource_name": obj.external_resource_name,
                "priority": obj.priority,
                "bucket": obj.bucket,
            })
        except self.model.DoesNotExist:
            pass
        return initial


class ActionTransferView(BaseTransferView):
    model = Action
    pk_field = "pk"
    owner_field = "created_by"


class ActionPublishView(ContentEditorMixin, PublishView):
    model = Action
    slug_field = 'title_slug'
    pk_url_kwarg = 'pk'

    def get_object(self, kwargs):
        """Actions may have have duplicates title_slug values, so we need to
        explicitly construct the lookup values."""
        params = {
            self.slug_field: kwargs.get(self.slug_field, None),
            self.pk_url_kwarg: kwargs.get(self.pk_url_kwarg, None),
        }
        return self.model.objects.get(**params)


class ActionUpdateView(ContentAuthorMixin, ReviewableUpdateMixin, UpdateView):
    model = Action
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"
    pk_url_kwarg = 'pk'
    form_class = ActionForm

    def get_success_url(self):
        return self.object.get_absolute_url()

    def post(self, request, *args, **kwargs):
        # Handle dealing with 2 forms.
        self.object = self.get_object()
        form = self.get_form()
        trigger_form = ActionTriggerForm(
            request.POST,
            instance=self.object.default_trigger,
            prefix="trigger"
        )
        if form.is_valid() and trigger_form.is_valid():
            return self.form_valid(form, trigger_form)
        else:
            return self.form_invalid(form, trigger_form)

    def get_form(self, form_class=None):
        """Include the user as a keyword arg for the form class."""
        form_class = form_class or self.get_form_class()
        kwargs = self.get_form_kwargs()
        kwargs['user'] = self.request.user
        return form_class(**kwargs)

    def form_valid(self, form, trigger_form):
        self.object = form.save()
        default_trigger = trigger_form.save(commit=False)
        trigger_name = "Default: {0}-{1}".format(self.object, self.object.id)
        default_trigger.name = trigger_name
        default_trigger.save()
        self.object.default_trigger = default_trigger
        self.object.save(updated_by=self.request.user)
        # call up to the superclass's method to handle state transitions
        super().form_valid(form)
        messages.success(self.request, "Your notification has been saved")
        return redirect(self.get_success_url())

    def form_invalid(self, form, trigger_form):
        ctx = self.get_context_data(form=form, trigger_form=trigger_form)
        return self.render_to_response(ctx)

    def get_context_data(self, **kwargs):
        context = super(ActionUpdateView, self).get_context_data(**kwargs)
        context['Action'] = self.model

        # pre-populate some dynamic content displayed to the user regarding
        # an action's parent behavior.
        context['behaviors'] = Behavior.objects.values(
            "id", "description", "informal_list"
        )

        # Include a form for the default trigger
        if 'trigger_form' not in context:
            context['trigger_form'] = ActionTriggerForm(
                instance=self.object.default_trigger,
                prefix="trigger"
            )

        # And the ability to disable it.
        context['disable_trigger_form'] = DisableTriggerForm()
        return context


def disable_trigger(request, pk, title_slug):
    """A Simple view to remove an action's default trigger."""
    action = get_object_or_404(Action, pk=pk)
    if request.method == "POST":
        form = DisableTriggerForm(request.POST)
        if form.is_valid():
            action.disable_default_trigger()
            messages.success(request, "The default trigger has been removed.")
        else:
            messages.error(request, "Sorry, we could not remove the trigger.")
    return redirect(action.get_absolute_url())


class ActionDeleteView(ContentEditorMixin, ContentDeleteView):
    model = Action
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('goals:index')


class OrganizationListView(StaffRequiredMixin, ListView):
    model = Organization
    context_object_name = 'organizations'
    template_name = "goals/organization_list.html"


class OrganizationDetailView(StaffRequiredMixin, DetailView):
    queryset = Organization.objects.all()
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"


class OrganizationCreateView(StaffRequiredMixin, CreateView):
    model = Organization
    form_class = OrganizationForm
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"

    def get_success_url(self):
        url = super().get_success_url()
        messages.success(self.request, "Your organization has been created.")
        return url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organizations'] = Organization.objects.all()
        return context


class OrganizationUpdateView(StaffRequiredMixin, UpdateView):
    model = Organization
    form_class = OrganizationForm
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"

    def get_success_url(self):
        url = super().get_success_url()
        messages.success(self.request, "Your organization has been saved")
        return url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organizations'] = Organization.objects.all()
        return context


class OrganizationDeleteView(StaffRequiredMixin, DeleteView):
    model = Organization
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
    success_url = reverse_lazy('goals:organization-list')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.members.count() > 0:
            msg = "You cannot remove an Organization with members."
            return HttpResponseForbidden(msg)
        result = super().delete(request, *args, **kwargs)
        messages.success(
            request,
            "Your organization ({}) has been deleted.".format(obj.name)
        )
        return result


class ProgramListView(StaffRequiredMixin, ListView):
    """A list of all programs (not filtered by Organization)."""
    model = Program
    context_object_name = 'programs'
    template_name = "goals/program_list.html"


class ProgramDetailView(StaffRequiredMixin, DetailView):
    queryset = Program.objects.all()
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization'] = self.object.organization
        return context


class ProgramCreateView(StaffRequiredMixin, CreateView):
    model = Program
    form_class = ProgramForm
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"

    def _get_organization(self, pk):
        try:
            return Organization.objects.get(pk=pk)
        except Organization.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        self.organization = self._get_organization(kwargs['pk'])
        if self.organization is None:
            return HttpResponseNotFound(render_to_string('404.html'))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.organization = self._get_organization(kwargs['pk'])
        if self.organization is None:
            return HttpResponseNotFound(render_to_string('404.html'))
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.organization
        return kwargs

    def get_success_url(self):
        messages.success(self.request, "Your program has been created.")
        return self.organization.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization'] = self.organization
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.organization = self.organization
        self.object.save()
        form.save_m2m()  # save the categories & goals
        return redirect(self.get_success_url())


class ProgramUpdateView(StaffRequiredMixin, UpdateView):
    model = Program
    form_class = ProgramForm
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.object.organization
        return kwargs

    def get_success_url(self):
        messages.success(self.request, "Your program has been saved")
        return self.object.organization.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization'] = self.object.organization
        return context


class ProgramDeleteView(StaffRequiredMixin, DeleteView):
    model = Program
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
    success_url = reverse_lazy('goals:program-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization'] = self.object.organization
        return context

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.members.exists():
            msg = "You cannot remove an Program with members."
            return HttpResponseForbidden(msg)
        result = super().delete(request, *args, **kwargs)
        messages.success(
            request,
            "Your program ({}) has been deleted.".format(obj.name)
        )
        return result


class PackageListView(ContentViewerMixin, ListView):
    queryset = Category.objects.packages(published=False)
    context_object_name = 'categories'
    template_name = "goals/package_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class PackageDetailView(ContentViewerMixin, DetailView):
    queryset = Category.objects.packages(published=False)
    context_object_name = 'category'
    template_name = "goals/package_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        editor = any([
            self.request.user.is_staff,
            self.request.user.has_perm('goals.publish_category'),
            self.request.user in self.object.contributors.all()
        ])
        context['is_editor'] = editor
        if editor:
            context['enrollments'] = self.object.packageenrollment_set.all()
        return context


@permission_required(ContentPermissions.package_managers)
def package_enrollment_user_details(request, package_id, user_id):
    User = get_user_model()
    user = get_object_or_404(User, pk=user_id)
    category = get_object_or_404(Category, pk=package_id)

    ctx = {
        'is_editor': is_content_editor(request.user),
        'package_user': user,
        'category': category,
        'packages': user.packageenrollment_set.all(),
    }
    return render(request, "goals/package_enrollment_user_details.html", ctx)


class PackageEnrollmentDeleteView(PackageManagerMixin, DeleteView):
    model = PackageEnrollment
    success_url = reverse_lazy('goals:package-list')

    def get_package_data(self, package):
        user = package.user
        # UserGoals, UserBehaviors, UserActions
        goals = package.goals.values_list('pk', flat=True)
        user_goals = user.usergoal_set.filter(goal__id__in=goals)
        user_behaviors = user.userbehavior_set.filter(behavior__goals__id__in=goals)
        behaviors = user_behaviors.values_list('behavior', flat=True)
        user_actions = user.useraction_set.filter(action__behavior__id__in=behaviors)

        # UserCompletedActions
        ucas = UserCompletedAction.objects.filter(useraction__in=user_actions)

        return {
            'user_goals': user_goals,
            'user_behaviors': user_behaviors,
            'user_actions': user_actions,
            'ucas': ucas,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        package = self.get_object()
        data = self.get_package_data(package)

        user_goals = data['user_goals']
        user_behaviors = data['user_behaviors']
        user_actions = data['user_actions']

        ucas = data['ucas']
        ucas_count = ucas.count()
        ucas_completed = ucas.filter(state=UserCompletedAction.COMPLETED).count()
        ucas_dismissed = ucas.filter(state=UserCompletedAction.DISMISSED).count()
        ucas_snoozed = ucas.filter(state=UserCompletedAction.SNOOZED).count()

        context['category'] = package.category
        context['package'] = package
        context['package_user'] = package.user
        context['user_goals'] = user_goals
        context['user_behaviors'] = user_behaviors
        context['user_actions'] = user_actions
        context['ucas_count'] = ucas_count
        context['ucas_completed'] = ucas_completed
        context['ucas_dismissed'] = ucas_dismissed
        context['ucas_snoozed'] = ucas_snoozed
        return context

    def delete(self, request, *args, **kwargs):
        # Remove the user's selected content that's within the package.
        package = self.get_object()
        data = self.get_package_data(package)
        for obj in data.values():
            obj.delete()
        messages.success(
            request,
            "The Package Enrollment for {} was removed".format(package.user)
        )
        return super().delete(request, *args, **kwargs)


class PackageEnrollmentView(ContentAuthorMixin, FormView):
    """Allow a user with *Author* permissions to automatically enroll users
    in a *package* of content. This will do the following:

    1. Create user accounts if they don't already exist.
    2. Assign users to all of the content in the package (i.e. create the
       intermediary UserAction, UserBehavior, UserGoal, and UserCategory objects)
       as if the user navigated through the app and selected them.
    3. Send the user an email letting them know they've been enrolled.

    """
    template_name = "goals/package_enroll.html"
    form_class = PackageEnrollmentForm

    def _can_access(self):
        # Determine if a user should be able to access this view.
        # REQUIRES self.category.
        return any([
            self.request.user.is_staff,
            self.request.user.has_perm('goals.publish_goal'),
            self.request.user in self.category.contributors.all()
        ])

    def get_success_url(self):
        return self.category.get_view_enrollment_url()

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.category, **self.get_form_kwargs())

    def get(self, request, *args, **kwargs):
        self.category = get_object_or_404(Category, pk=kwargs.get('pk'))
        form = self.get_form()
        return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        self.category = get_object_or_404(Category, pk=kwargs.pop('pk', None))
        if not self._can_access():
            return HttpResponseForbidden()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        # create user enrollment objects.
        goals = form.cleaned_data['packaged_goals']
        emails = form.cleaned_data['email_addresses']
        prevent_triggers = form.cleaned_data.get('prevent_custom_triggers', False)

        # Create enrollments if necessary.
        enrollments = PackageEnrollment.objects.batch_enroll(
            emails,
            self.category,
            goals,
            by=self.request.user,
            prevent_triggers=prevent_triggers
        )

        # send a link to the package enrollment not the user.
        send_package_enrollment_batch(self.request, enrollments)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        if not self._can_access():
            context['form'] = None
        return context


@permission_required(ContentPermissions.authors)
def package_calendar(request, pk):
    category = get_object_or_404(Category, pk=pk)
    start = request.GET.get('d', None)

    if start is None:
        # Start on the first day of the current month
        start = local_now(request.user)
        start = to_localtime(datetime(start.year, start.month, start.day), request.user)
    elif len(start) == len('yyyy-mm-dd'):
        year, month, day = start.split('-')
        start = to_localtime(datetime(int(year), int(month), int(day)), request.user)
    else:
        year, month = start.split('-')
        start = to_localtime(datetime(int(year), int(month), 1), request.user)

    # Include recurrences for actions that have both a default trigger AND
    # where those triggers have a time (otherwise they're essentially invalid)
    actions = category.actions.filter(
        default_trigger__isnull=False,
        default_trigger__time__isnull=False  # exclude invalid triggers
    )

    # note: start calendar on suday (6)
    cal = Calendar(firstweekday=6).monthdatescalendar(start.year, start.month)
    action_data = []
    stop_on_completes = defaultdict(int)  # Action.id to number of iterations
    contains_relative_reminders = False
    for action in actions:
        kwargs = {'days': 31}  # params for get_occurances
        if action.default_trigger.is_relative:
            # XXX: Temporarily set the trigger's start date, so this date
            # gets used when generating recurrences (which is how this will
            # work when a user selects the action). Additionally, we need to
            # temporarily assign a user (the logged in user) to make this work.
            action.default_trigger.user = request.user
            start_on = action.default_trigger.relative_trigger_date(start)
            action.default_trigger.trigger_date = start_on

        # include some meta-data for the stop-on-complete actions
        action.stop_on_complete = action.default_trigger.stop_on_complete

        for dt in action.default_trigger.get_occurences(**kwargs):
            stop_counter = None  # A counter for the stop_on_complete triggers.
            if action.stop_on_complete:
                stop_on_completes[action.id] += 1
                stop_counter = stop_on_completes[action.id]
            action_data.append((dt.date(), dt, action, stop_counter))

        # include a list of goal-ids in the action
        action.goal_ids = list(action.behavior.goals.values_list('id', flat=True))
        action.is_relative = action.default_trigger.is_relative
        if action.default_trigger.is_relative:
            contains_relative_reminders = True

    action_data = sorted(action_data, key=lambda d: d[1].strftime("%Y%m%d%H%M"))

    goals = list(category.goals.values_list('id', 'title'))
    ctx = {
        'is_editor': is_content_editor(request.user),
        'today': local_now(request.user),
        'category': category,
        'actions': action_data,
        'calendar': cal,
        'starting_date': start,
        'next_date': (cal[-1][-1] + timedelta(days=1)).strftime("%Y-%m"),
        'prev_date': (cal[0][0] - timedelta(days=1)).strftime("%Y-%m"),
        'goals': goals,
        'contains_relative_reminders': contains_relative_reminders,
    }
    return render(request, "goals/package_calendar.html", ctx)


@permission_required(ContentPermissions.authors)
def enrollment_cta_email(request, pk):
    """Let us send an arbitrary CTA email to users enrolled in a package."""
    category = get_object_or_404(Category, pk=pk)
    enrollments = category.packageenrollment_set.filter(accepted=True)

    if request.method == "POST":
        form = CTAEmailForm(request.POST)
        if form.is_valid():
            params = {
                'cta_link': form.cleaned_data['link'],
                'cta_text': form.cleaned_data['link_text'],
                'message': form.cleaned_data['message'],
                'subject': form.cleaned_data['subject'],
            }
            send_package_cta_email(request, enrollments, **params)
            messages.success(request, "Your message has been sent")
            return redirect(category.get_view_enrollment_url())
    else:
        form = CTAEmailForm()

    ctx = {'form': form, 'category': category, 'enrollments': enrollments}
    return render(request, "goals/package_enrollment_cta_email.html", ctx)


@permission_required(ContentPermissions.authors)
def enrollment_reminder(request, pk):
    """Let us send a reminder email to users that have not accepted the
    enrollment."""
    category = get_object_or_404(Category, pk=pk)
    enrollments = category.packageenrollment_set.filter(accepted=False)

    if request.method == "POST":
        form = EnrollmentReminderForm(request.POST)
        if form.is_valid():
            msg = form.cleaned_data['message']
            send_package_enrollment_batch(request, enrollments, message=msg)
            messages.success(request, "Your message has been sent")
            return redirect(category.get_view_enrollment_url())
    else:
        form = EnrollmentReminderForm()

    ctx = {'form': form, 'category': category, 'enrollments': enrollments}
    return render(request, "goals/package_enrollment_reminder.html", ctx)


# TODO: NEEDS TESTS.
def accept_enrollment(request, pk):
    """This view lets new users "claim" their account, set a password, & agree
    to some terms/conditions and a consent form for each Package/Category,
    before giving them a link to the app.

    Existing users who are being enrolled in a new Package/Category will have
    the option to just accept the consent form.

    """
    accept_form = None
    has_form_errors = False
    password_form = None
    user_form = None

    package = get_object_or_404(PackageEnrollment, pk=pk)

    if request.method == "POST" and package.user.is_active:
        # An existing user is being enrolled in a new package.
        accept_form = AcceptEnrollmentForm(request.POST, prefix="aef")
        if accept_form.is_valid():
            # Indicate their acceptance of the consent (The form isn't
            # valid without doing this)
            package.accept()
            request.session['user_id'] = package.user.id
            request.session['package_ids'] = [package.id]
            logger.info("Existing user accepted PackageEnrollment: {}".format(pk))
            return redirect(reverse("goals:accept-enrollment-complete"))
        else:
            has_form_errors = True
    elif request.method == "POST":
        # This is for a new user
        user_form = UserForm(request.POST, instance=package.user, prefix="uf")
        password_form = SetNewPasswordForm(request.POST, prefix="pf")
        accept_form = AcceptEnrollmentForm(request.POST, prefix="aef")
        forms_valid = [
            user_form.is_valid(), password_form.is_valid(), accept_form.is_valid()
        ]
        if all(forms_valid):
            # Be sure to activate their account.
            user = user_form.save()
            user.is_active = True
            user.set_password(password_form.cleaned_data['password'])
            user.save()

            # Now, indicate their acceptance of the consent (The form isn't
            # valid without doing this)
            package.accept()
            request.session['user_id'] = package.user.id
            request.session['package_ids'] = [package.id]
            logger.info("New user accepted PackageEnrollment: {}".format(pk))
            return redirect(reverse("goals:accept-enrollment-complete"))
        else:
            has_form_errors = True

    elif package.user.is_active:
        # they only need the Accept form, not the user-creation stuff.
        accept_form = AcceptEnrollmentForm(prefix="aef", package=package)

    else:
        user_form = UserForm(instance=package.user, prefix="uf")
        password_form = SetNewPasswordForm(prefix="pf")
        accept_form = AcceptEnrollmentForm(prefix="aef", package=package)

    context = {
        'user': package.user,
        'user_form': user_form,
        'password_form': password_form,
        'accept_form': accept_form,
        'has_form_errors': has_form_errors,
        'package': package,
        'category': package.category,
    }
    return render(request, 'goals/accept_enrollment.html', context)


class AcceptEnrollmentCompleteView(TemplateView):
    template_name = "goals/accept_enrollment_complete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['android_url'] = settings.PLAY_APP_URL
        context['ios_url'] = settings.IOS_APP_URL
        context['packages'] = PackageEnrollment.objects.filter(
            id__in=self.request.session.get("package_ids", [])
        )
        return context


@user_passes_test(is_contributor, login_url='/goals/')
def package_report(request, pk):
    category = get_object_or_404(Category, pk=pk)
    enrollees = category.packageenrollment_set.values_list('user', flat=True)

    today = timezone.now()
    days_ago = int(request.GET.get('days_ago', 30))
    from_date = today - timedelta(days=days_ago)

    # Are Users Completing Actions?
    uca_labels = []
    completed = []
    snoozed = []
    dismissed = []
    for day in dates_range(days_ago):
        uca_labels.append(day.strftime("%F"))
        params = {
            'user__in': enrollees,
            'updated_on__year': day.year,
            'updated_on__month': day.month,
            'updated_on__day': day.day,
        }
        results = UserCompletedAction.objects.filter(**params)
        completed.append(results.filter(state=UserCompletedAction.COMPLETED).count())
        snoozed.append(results.filter(state=UserCompletedAction.SNOOZED).count())
        dismissed.append(results.filter(state=UserCompletedAction.DISMISSED).count())

    completed_data = {'label': 'Completed Actions', 'data': completed}
    snoozed_data = {'label': 'Snoozed Actions', 'data': snoozed}
    dismissed_data = {'label': 'Dismissed Actions', 'data': dismissed}
    uca_datasets = [(completed_data, snoozed_data, dismissed_data), ]

    # Popular Goals
    usergoals = UserGoal.objects.filter(
        user__in=enrollees,
        goal__categories=category
    ).values_list("goal__title", flat=True).distinct()
    usergoals = Counter(usergoals)
    usergoals_datasets = {
        'label': 'Selected Goals',
        'data': list(usergoals.values())
    }
    usergoals_labels = list(usergoals.keys())

    # How long ago each enrollee's userprofile was updated. This corresponds
    # to opening the app (since their timezone is updated every time).
    profiles = UserProfile.objects.filter(user__in=enrollees)
    accessed = profiles.datetimes('updated_on', 'day')  # TODO: change to updated_on
    accessed = Counter([timesince(dt) for dt in accessed])
    accessed = sorted(accessed.items())
    accessed_labels = [a[0] for a in accessed]
    accessed_datasets = {
        'label': 'App Last Accessed',
        'data': [a[1] for a in accessed]
    }

    # Count the unkown dates (which may happen because we haven't always tracked
    unknown = profiles.filter(updated_on__isnull=True).count()
    if unknown:
        accessed_labels += ['Unkown']
        accessed_datasets['data'] += [unknown]

    context = {
        'category': category,
        'enrollees': enrollees,
        'days_ago': days_ago,
        'today': today,
        'from_date': from_date,
        'uca_labels': uca_labels,
        'uca_datasets': uca_datasets,
        'accessed_labels': accessed_labels,
        'accessed_datasets': accessed_datasets,
        'usergoals_datasets': usergoals_datasets,
        'usergoals_labels': usergoals_labels,
    }
    return render(request, 'goals/package_report.html', context)


def file_upload(request, object_type, pk):
    """Handler for drag-n-drop file uploads for Goals, Behaviors, and Actions.

    NOTE: This only works for the `icon` field at the moment.
    See: https://docs.djangoproject.com/en/1.8/topics/http/file-uploads/

    """
    # The supported models.
    objects = {
        'goal': (Goal, UploadImageForm),
        'action': (Action, UploadImageForm),
        'behavior': (Behavior, UploadImageForm),
    }
    try:
        model, form_class = objects.get(object_type, (None, None))
        obj = get_object_or_404(model, pk=pk)
    except ValueError:
        logger.error("File upload failed {}.{}".format(object_type, pk))
        return HttpResponseBadRequest()

    errors = ""
    if request.method == "POST":
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            obj.icon = request.FILES['file']
            obj.save()
        else:
            errors = str(form.errors)
        return HttpResponse()

    # Assume something went wrong.
    logger.error("File upload failed {}".format(errors))
    return HttpResponseBadRequest(errors)


def admin_batch_assign_keywords(request):
    if request.method == "POST":
        goal_ids = request.POST.get('ids', '')
        goals = Goal.objects.filter(id__in=goal_ids.split('+'))
        keywords = request.POST.get('keywords', '')
        keywords = keywords.split(",")
        for goal in goals:
            goal.keywords = goal.keywords + keywords
            goal.save()
        msg = "Keywords added to {0} goals.".format(goals.count())
        messages.success(request, msg)
        return redirect('/admin/goals/goal/')
    else:
        goal_ids = request.GET.get('ids', '')
        goals = Goal.objects.filter(id__in=goal_ids.split('+'))

    context = {
        'app_label': 'goals',
        'title': 'Add Keywords',
        'opts': {'app_label': 'goals'},
        'original': None,
        'adminform': None,
        'goal_ids': goal_ids,
        'goals': goals,
    }
    return render(request, 'goals/admin_batch_assign_keywords.html', context)


@job
def _duplicate_category_content(category, prefix=None):
    """Given a category and an optional prefix, duplicate all of it's content;
    NOTE: This is an async RQ task, defined here, because otherwise the
    view below won't be able to import it (or least I couldn't get it to
    work)."""
    if prefix:
        category.duplicate_content(prefix)
    else:
        category.duplicate_content()


@user_passes_test(staff_required, login_url='/')
def duplicate_content(request, pk, title_slug):
    category = get_object_or_404(Category, pk=pk, title_slug=title_slug)
    if request.method == "POST":
        form = TitlePrefixForm(request.POST)
        if form.is_valid():
            prefix = form.cleaned_data['prefix']
            _duplicate_category_content.delay(category, prefix)
            msg = (
                "Your content is being duplicated and should be available in "
                "about a minute."
            )
            messages.success(request, msg)
            return redirect("goals:category-list")
    else:
        form = TitlePrefixForm()

    context = {
        'category': category,
        'form': form,
    }
    return render(request, 'goals/duplicate_content.html', context)


class DebugToolsView(TemplateView):
    template_name = "goals/debug_tools.html"


@user_passes_test(staff_required, login_url='/')
def debug_sequence(request):
    """
    List all of the user's selected content ordered by "next_in_sequence"

    """
    User = get_user_model()
    email = request.GET.get('email_address', None)
    data = None

    goals = []
    behaviors = []
    actions = []

    if email is None:
        form = EmailForm()
    else:
        form = EmailForm(initial={'email_address': email})
        try:
            user = User.objects.get(email__icontains=email)
            data = get_next_in_sequence_data(user, print_them=False)

            for goal, bevs in data.items():
                goals.append(goal)
                for behavior, actions in bevs.items():
                    behaviors.append(behavior)
                    actions.extend(list(actions))

        except (User.DoesNotExist, User.MultipleObjectsReturned):
            messages.error(request, "Could not find that user")

    context = {
        'form': form,
        'email': email,
        'data': data,
        'goals': goals,
        'behaviors': behaviors,
        'actions': actions,
    }
    return render(request, 'goals/debug_sequence.html', context)


@user_passes_test(staff_required, login_url='/')
def debug_priority_notifications(request):
    """

    """
    User = get_user_model()
    useractions = None
    email = request.GET.get('email_address', None)
    devices = None

    if email is None:
        form = EmailForm()
    else:
        form = EmailForm(initial={'email_address': email})
        try:
            user = User.objects.get(email__icontains=email)

            # HIGH-priority UserActions
            useractions = user.useraction_set.filter(
                action__priority=Action.HIGH
            ).prefetch_related('action', 'custom_trigger').order_by("next_trigger_date")

            # Get the user's devices
            devices = user.gcmdevice_set.values_list('device_name', 'device_type')
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            messages.error(request, "Could not find that user")

    context = {
        'devices': devices,
        'form': form,
        'email': email,
        'useractions': useractions,
    }
    return render(request, 'goals/debug_priority_notifications.html', context)


@user_passes_test(staff_required, login_url='/')
def debug_notifications(request):
    """A view to allow searching by email addresss, then listing all UserActions
    for a day, with all of the sheduled GCMNotifications for that user.

    """
    # How many UserActions/CustomActions to display
    num_items = int(request.GET.get('n', 25))

    User = get_user_model()
    customactions = None
    useractions = None
    next_user_action = None
    today = None
    next_in_sequence = []
    upcoming_useractions = []
    upcoming_customactions = []
    user_queues = OrderedDict()
    devices = None

    email = request.GET.get('email_address', None)

    if email is None:
        form = EmailForm()
    else:
        form = EmailForm(initial={'email_address': email})
        try:
            user = User.objects.get(email__icontains=email)
            today = local_day_range(user)

            # UserActions
            useractions = user.useraction_set.all().distinct()[:num_items]
            next_in_sequence = get_next_useractions_in_sequence(user)

            # Custom Actions
            customactions = user.customaction_set.all()
            customactions = customactions.order_by("next_trigger_date")
            customactions = customactions.distinct()[:num_items]

            next_user_action = user_feed.next_user_action(user)
            upcoming_useractions = user_feed.todays_actions(user)
            upcoming_customactions = user_feed.todays_customactions(user)
            for ua in useractions:
                ua.upcoming = ua in upcoming_useractions
            for ca in customactions:
                ca.upcoming = ca in upcoming_customactions

            # The user's notification queue
            dt = today[0]
            days = sorted([dt + timedelta(days=i) for i in range(0, 7)])
            for dt in days:
                user_queues[dt.strftime("%Y-%m-%d")] = {}

            for dt in days:
                qdata = queue.UserQueue.get_data(user, date=dt)
                # data for a user queue is a dict that looks like this:
                # {'uq:1:2016-04-25:count':  0,
                #  'uq:1:2016-04-25:high':   [],
                #  'uq:1:2016-04-25:low':    [],
                #  'uq:1:2016-04-25:medium': []}
                for key, content in qdata.items():
                    parts = key.split(':')
                    datestring = parts[2]
                    key = parts[3]
                    user_queues[datestring][key] = content

            # Get the user's devices
            devices = user.gcmdevice_set.values_list('device_name', 'device_type')
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            messages.error(request, "Could not find that user")

    context = {
        'devices': devices,
        'num_items': num_items,
        'form': form,
        'email': email,
        'useractions': useractions,
        'customactions': customactions,
        'next_user_action': next_user_action,
        'next_in_sequence': next_in_sequence,
        'upcoming_useractions': upcoming_useractions,
        'upcoming_customactions': upcoming_customactions,
        'today': today,
        'user_queues': user_queues,
    }
    return render(request, 'goals/debug_notifications.html', context)


@user_passes_test(staff_required, login_url='/')
def debug_feed(request):
    """Ugh. List the data for the feed, the useractions with a "today"
    next_trigger_date, and the created GCMMessages for today side-by-side.

    """
    User = get_user_model()
    today = None
    useractions = None
    feed_useractions = None
    progress = None
    notifs = None
    ucas = None
    email = request.GET.get('email_address', None)

    if email is None:
        form = EmailForm()
    else:
        form = EmailForm(initial={'email_address': email})
        try:
            user = User.objects.get(email__icontains=email)
            today = local_day_range(user)

            # UserActions
            useractions = user.useraction_set.published()
            useractions = useractions.filter(next_trigger_date__range=today)
            useractions = useractions.distinct()

            # UserCompletedActions
            ucas = user.usercompletedaction_set.filter(updated_on__range=today)

            # GCMMessages
            notifs = user.gcmmessage_set.filter(deliver_on__range=today)

            # Feed data
            feed_useractions = user_feed.todays_actions(user)
            progress = user_feed.todays_actions_progress(user)

        except (User.DoesNotExist, User.MultipleObjectsReturned):
            messages.error(request, "Could not find that user")

    context = {
        'form': form,
        'today': today,
        'email': email,
        'notifs': notifs,
        'useractions': useractions,
        'ucas': ucas,
        'feed_useractions': feed_useractions,
        'progress': progress,
    }
    return render(request, 'goals/debug_feed.html', context)


@user_passes_test(staff_required, login_url='/')
def debug_progress(request):
    """A view to allow searching by email addresss then view and
    analyze their DailyProgress info.

    """
    # -------------------------------------------------------------------------
    # TODO: Figure out how to compile data for user "streaks", ie. days in a
    # row in which a user has interacted with the app.
    # -------------------------------------------------------------------------
    # UserCompletedAction --> state=completed, updated_on dates
    # DailyProgress has numbers aggregated for completed, snoozed, dismissed
    # -------------------------------------------------------------------------

    User = get_user_model()
    email = request.GET.get('email_address', None)
    user = None
    form = EmailForm(initial={'email_address': email})
    next_goals = []
    next_behaviors = []
    next_actions = []
    streaks = []

    try:
        user = User.objects.get(email__icontains=email)
    except (User.DoesNotExist, User.MultipleObjectsReturned):
        messages.error(request, "Could not find that user")
        return redirect(reverse('goals:debug_progress'))
    except ValueError:
        user = None

    today = timezone.now()
    since = int(request.GET.get('since', 30))
    from_date = today - timedelta(days=since)
    daily_progresses = DailyProgress.objects.filter(
        user=user,
        updated_on__gte=from_date
    )

    # Completed Actions/Behaviors/Goals.
    completed = {'actions': [], 'behaviors': [], 'goals': []}
    if user:
        ucas = user.usercompletedaction_set.all()
        completed['actions'] = ucas.filter(updated_on__gte=from_date)
        behaviors = user.userbehavior_set.filter(completed=True)
        completed['behaviors'] = behaviors.filter(completed_on__gte=from_date)
        goals = user.usergoal_set.filter(completed=True)
        completed['goals'] = goals.filter(completed_on__gte=from_date)

        # NEXT in sequence objeccts.
        next_goals = user.usergoal_set.next_in_sequence(published=True)
        next_behaviors = user.userbehavior_set.next_in_sequence(
            goals=next_goals.values_list('goal', flat=True), published=True)
        next_actions = user.useraction_set.next_in_sequence(
            next_behaviors.values_list('behavior', flat=True), published=True)
        next_actions = next_actions.order_by("next_trigger_date")

        # Streaks.
        # ---------------------------------------------------------------------
        # Days in a row in which the user said "got it" (completed) or
        # dismissed/snoozed an action.
        def _fill_streaks(input_values, since, default_tup=()):
            """fills in  data for missing dates"""
            dates = sorted([dt.date() for dt in dates_range(since)])
            index = 0  # index of the last, non-generated item
            for dt in dates:
                if index < len(input_values) and input_values[index][0] == dt:
                    yield input_values[index]
                    index += 1
                else:
                    data = (dt, ) + default_tup
                    yield data

        # Pulling from DailyProgress
        streaks = daily_progresses.values_list(
            'actions_completed', 'actions_snoozed', 'actions_dismissed',
            'updated_on'
        ).order_by('updated_on')
        streaks = [
            (
                updated.date(),
                True if comp > 0 else (snoozed > 0 or dismissed > 0),
                comp,
                snoozed,
                dismissed
            )
            for comp, snoozed, dismissed, updated in streaks
        ]
        streaks = list(_fill_streaks(streaks, since, (False, 0, 0, 0)))
        # ---------------------------------------------------------------------

    context = {
        'streaks': streaks,
        'streaks_dates': [t[0].strftime("%Y-%m-%d") for t in streaks],
        'email': email,
        'searched_user': user,
        'since': since,
        'form': form,
        'today': today,
        'from_date': from_date,
        'daily_progresses': daily_progresses,
        'completed': completed,
        'next_goals': next_goals,
        'next_behaviors': next_behaviors,
        'next_actions': next_actions,
    }
    return render(request, 'goals/debug_progress.html', context)


class ReportsView(ContentViewerMixin, TemplateView):
    """This view simply renders a template that lists the available reports
    with a short description of each."""
    template_name = "goals/reports.html"


class ReportPopularView(ContentViewerMixin, TemplateView):
    template_name = "goals/report_popular.html"

    def get(self, request, *args, **kwargs):
        """Include the most popular content in the conext prior to rendering"""
        context = self.get_context_data(**kwargs)
        context['popular_categories'] = popular_categories()
        context['popular_goals'] = popular_goals()
        context['popular_behaviors'] = popular_behaviors()
        context['popular_actions'] = popular_actions()
        return self.render_to_response(context)


@user_passes_test(staff_required, login_url='/')
def report_triggers(request):
    triggers = Trigger.objects.all()
    total_trigger_count = triggers.count()
    custom_trigger_count = triggers.filter(user__isnull=False).count()

    with_recurrences = triggers.filter(recurrences__isnull=False).count()

    time_and_date_only = triggers.filter(
        trigger_date__isnull=False,
        time__isnull=False,
        recurrences__isnull=True
    ).count()

    time_only = triggers.filter(
        time__isnull=False,
        trigger_date__isnull=True,
        recurrences__isnull=True
    ).count()

    date_only = triggers.filter(
        trigger_date__isnull=False,
        time__isnull=True,
        recurrences__isnull=True
    ).count()

    # Count all the recurrence options
    custom_triggers = triggers.filter(
        user__isnull=False,
        recurrences__isnull=False
    )
    custom_recurrences = []
    for t in custom_triggers:
        custom_recurrences.append(t.recurrences_as_text())
    custom_recurrences = Counter(custom_recurrences)

    # Counts for time of day / frequency
    tods = Trigger.objects.filter(time_of_day__gt='')
    tod_counter = Counter(tods.values_list("time_of_day", flat=True))
    freqs = Trigger.objects.filter(frequency__gt='')
    freq_counter = Counter(freqs.values_list("frequency", flat=True))

    context = {
        'total_trigger_count': total_trigger_count,
        'custom_trigger_count': custom_trigger_count,
        'default_trigger_count': total_trigger_count - custom_trigger_count,
        'with_recurrences': with_recurrences,
        'time_and_date_only': time_and_date_only,
        'time_only': time_only,
        'date_only': date_only,
        'custom_recurrences': custom_recurrences.most_common(20),
        'tod_counter': dict(tod_counter),
        'freq_counter': dict(freq_counter),
    }
    return render(request, 'goals/report_triggers.html', context)


@user_passes_test(staff_required, login_url='/')
def report_authors(request):
    author_criteria = None
    author = request.GET.get('email', None)
    if author is not None:
        author_criteria = Q(created_by__email__istartswith=author.strip())

    # Count of who's got how many items in what state.
    states = ['draft', 'published', 'pending-review', 'declined']
    goals = {}
    behaviors = {}
    actions = {}
    for state in states:
        items = Goal.objects.filter(state=state)
        if author_criteria:
            items = items.filter(author_criteria)
        items = items.values_list('created_by__email', flat=True)
        goals[state] = dict(Counter(items))

        items = Behavior.objects.filter(state=state)
        if author_criteria:
            items = items.filter(author_criteria)
        items = items.values_list('created_by__email', flat=True)
        behaviors[state] = dict(Counter(items))

        items = Action.objects.filter(state=state)
        if author_criteria:
            items = items.filter(author_criteria)
        items = items.values_list('created_by__email', flat=True)
        actions[state] = dict(Counter(items))

    context = {
        'goals': goals,
        'behaviors': behaviors,
        'actions': actions,
    }
    return render(request, 'goals/report_authors.html', context)


@user_passes_test(staff_required, login_url='/')
def report_actions(request):
    """Information about our Action content.

    This view contains code for several "sub reports". They are:

    - notif: List actions with "long" notifictation_text
    - desc: List actions with "long" description text
    - links: List actions whose more_info/descriptions contain links
    - triggers: Filter actions based on their default_triggers (whether they're
      dynamic, contain advanced options, or some combination of both).

    """
    limit = 100
    subreport = request.GET.get('sub', None)
    max_len = int(request.GET.get('len', 200))
    valid_options = [200, 300, 400, 600, 800, 1000]

    # Notifications will be shorter, so use a different set of valid lengths
    if subreport == "notif":
        valid_options = [90, 100, 150]

    if max_len not in valid_options:
        max_len = valid_options[0]

    actions = Action.objects.all()
    context = {
        'limit': limit,
        'actions': None,
        'total': actions.count(),
        'max_len': max_len,
        'len_options': valid_options,
        'subreport': subreport,
    }
    for state in ['draft', 'published', 'pending-review', 'declined']:
        key = "{}_count".format(state.replace('-', ''))
        data = {key: actions.filter(state=state).count()}
        context.update(data)

    if subreport == "desc":  # Long descriptions
        actions = actions.annotate(text_len=Length('description'))
        actions = actions.filter(text_len__gt=max_len).select_related('behavior')
        context['actions'] = actions.order_by('-text_len')[:limit]
        context['subreport_title'] = "Long Descriptions"
    elif subreport == "notif":  # Long notifiation text
        actions = actions.annotate(text_len=Length('notification_text'))
        actions = actions.filter(text_len__gt=max_len).select_related('behavior')
        context['actions'] = actions.order_by('-text_len')[:limit]
        context['subreport_title'] = "Long Notification Text"
    elif subreport == "links":  # description / more_info contains URLs
        actions = actions.filter(
            Q(description__icontains='http') |
            Q(more_info__icontains='http')
        )
        actions = actions.annotate(text_len=Length('description'))
        context['actions'] = actions[:limit]
        context['subreport_title'] = "Containing Links"
        context['len_options'] = []
    elif subreport == "triggers" and request.GET.get('trigger') == 'dynamic':
        # List dynamic triggers
        actions = actions.filter(
            default_trigger__time_of_day__isnull=False,
            default_trigger__frequency__isnull=False,
        )
        context['actions'] = actions[:limit]
        context['subreport_title'] = "Trigger options"
        context['len_options'] = []
        context['trigger'] = 'dynamic'
    elif subreport == "triggers" and request.GET.get('trigger') == 'advanced':
        actions = actions.filter(
            default_trigger__time_of_day__isnull=True,
            default_trigger__frequency__isnull=True,
        )
        context['actions'] = actions[:limit]
        context['subreport_title'] = "Trigger options"
        context['len_options'] = []
        context['trigger'] = 'advanced'
    elif subreport == "triggers" and request.GET.get('trigger') == 'time':
        actions = actions.filter(
            default_trigger__time_of_day__isnull=False,
            default_trigger__frequency__isnull=True,
        )
        context['actions'] = actions[:limit]
        context['subreport_title'] = "Trigger options"
        context['len_options'] = []
        context['trigger'] = 'time'
    elif subreport == "triggers" and request.GET.get('trigger') == 'freq':
        actions = actions.filter(
            default_trigger__time_of_day__isnull=True,
            default_trigger__frequency__isnull=False,
        )
        context['actions'] = actions[:limit]
        context['subreport_title'] = "Trigger options"
        context['len_options'] = []
        context['trigger'] = 'freq'
    elif subreport == "triggers" and request.GET.get('trigger') == 'none':
        actions = actions.filter(default_trigger__isnull=True)
        context['actions'] = actions[:limit]
        context['subreport_title'] = "Trigger options"
        context['len_options'] = []
        context['trigger'] = 'none'

    return render(request, 'goals/report_actions.html', context)


@user_passes_test(staff_required, login_url='/')
def report_engagement(request):
    """A report on User-engagement in the app.

    Questions:

    - are they checking in?
    - are they doing anything with notifications?
    - should we show aggregate data...
    - or make it searchable by user.

    """
    since = timezone.now() - timedelta(days=30)  # TODO: ability to change this scale

    dps = DailyProgress.objects.filter(created_on__gte=since, actions_total__gt=0)
    aggregates = dps.aggregate(
        Sum('actions_completed'),
        Sum('actions_snoozed'),
        Sum('actions_dismissed'),
    )
    # Do we have notification engagement data?
    has_engagement = all(aggregates.values())

    ca_aggregates = dps.aggregate(
        Sum('customactions_completed'),
        Sum('customactions_snoozed'),
        Sum('customactions_dismissed'),
    )
    # Do we have custom notification engagement data?
    has_ca_engagement = all(ca_aggregates.values())

    engagement = defaultdict(Counter)
    if has_engagement:
        # WANT: count daily values for each interaction, e.g.
        #   d[2016-05-14] = {'completed': 25, 'snooozed': 10, 'dismissed': 5}
        #   d[2016-05-15] = {'completed': 25, 'snooozed': 10, 'dismissed': 5}
        for dp in dps:
            dt = dp.created_on.strftime("%Y-%m-%d")
            engagement[dt]['snoozed'] += dp.actions_snoozed
            engagement[dt]['completed'] += dp.actions_completed
            engagement[dt]['dismissed'] += dp.actions_dismissed
        # now convert to a sorted list of tuples
        # (2016-01-02, snoozed, dismissed, completed)
        engagement = sorted([
            (t, data['snoozed'], data['dismissed'], data['completed'])
            for t, data in engagement.items()
        ])

    # Same as engagement, but for custom actions
    ca_engagement = defaultdict(Counter)
    if has_ca_engagement:
        for dp in dps:
            dt = dp.created_on.strftime("%Y-%m-%d")
            ca_engagement[dt]['snoozed'] += dp.customactions_snoozed
            ca_engagement[dt]['completed'] += dp.customactions_completed
            ca_engagement[dt]['dismissed'] += dp.customactions_dismissed

        ca_engagement = sorted([
            (t, data['snoozed'], data['dismissed'], data['completed'])
            for t, data in ca_engagement.items()
        ])

    context = {
        'since': since,
        'progresses': dps,
        'aggregates': aggregates,
        'ca_aggregates': ca_aggregates,
        'has_engagement': has_engagement,
        'engagement': engagement,
        'has_ca_engagement': has_ca_engagement,
        'ca_engagement': ca_engagement,
    }
    return render(request, 'goals/report_engagement.html', context)


@user_passes_test(staff_required, login_url='/')
def report_organization(request, pk=None):
    """A report on Organization member's selected content.

    If a `pk` is provided, we'll display info for that organization. Otherwise,
    we'll list the organizations.

    """
    N = 10  # The top N goals.

    try:
        org = Organization.objects.get(pk=pk)
        member_ids = org.members.values_list('pk', flat=True)
        org_cats = org.program_set.values_list('categories', flat=True)

        # All of the Goals selected by org members that aren't org-related goals.
        org_goals = UserGoal.objects.filter(
            user__in=member_ids,
            goal__categories__in=org_cats
        ).values_list("goal__title", flat=True)
        org_goals = Counter(org_goals).most_common(N)
        org_goals = sorted(org_goals, key=lambda t: t[1], reverse=True)

        nonorg_goals = UserGoal.objects.filter(user__in=member_ids)
        # Exclude the organization's program goals
        nonorg_goals = nonorg_goals.exclude(goal__categories__in=org_cats)
        # Exclude any goals in which users are globally auto-enrolled.
        nonorg_goals = nonorg_goals.exclude(
            goal__categories__selected_by_default=True
        )

        # User IDs for all of the org members who've selected content outside
        # of the organization's programs.
        public_users = set(nonorg_goals.values_list("user", flat=True))

        nonorg_goals = nonorg_goals.values_list("goal__title", flat=True)
        nonorg_goals = Counter(nonorg_goals).most_common(N)
        nonorg_goals = sorted(nonorg_goals, key=lambda t: t[1], reverse=True)

        # What % of org members select public goals.
        percentage = (len(public_users) / len(set(member_ids))) * 100

    except Organization.DoesNotExist:
        org = None
        org_goals = []
        nonorg_goals = []
        percentage = None

    context = {
        'organization': org,
        'organizations': Organization.objects.values_list("id", "name"),
        'organization_goals': org_goals,
        'non_organization_goals': nonorg_goals,
        'percentage': percentage,
    }
    return render(request, 'goals/report_organization.html', context)


def fake_api(request, option=None):
    """Return a 'fake' api response. This is a view that returns fake/dummy
    data for api endpoints that we may have removed; This will prevent an
    older version of the app from crashing when it tries to hit an endpoint.
    """
    if option in ['goalprogress', 'behaviorprogress']:
        # /api/users/behaviors/progress/
        # /api/users/goals/progress/
        return JsonResponse({
            "count": 0,
            "next": None,
            "previous": None,
            "results": []
        })

    elif option == 'goalprogressaverage':
        # /api/api/users/goals/progress/average/
        return JsonResponse({
            "text": "Great job! You're doing well!",
            "daily_checkin_avg": 0,
            "weekly_checkin_avg": 0,
            "better": True
        })

    return HttpResponseNotFound()
