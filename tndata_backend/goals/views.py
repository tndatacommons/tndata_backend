from calendar import Calendar
from collections import defaultdict, Counter
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Avg, Count, Q, Min, Max
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import timesince
from django.views.generic import DetailView, FormView, ListView, TemplateView, View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.utils import timezone

from django_fsm import TransitionNotAllowed
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
    AcceptEnrollmentForm,
    ActionTriggerForm,
    BehaviorForm,
    CategoryForm,
    ContentAuthorForm,
    CTAEmailForm,
    DisableTriggerForm,
    EnrollmentReminderForm,
    GoalForm,
    PackageEnrollmentForm,
    TitlePrefixForm,
    UploadImageForm,
)
from . mixins import (
    ContentAuthorMixin, ContentEditorMixin, ContentViewerMixin,
    PackageManagerMixin, ReviewableUpdateMixin,
)
from . models import (
    Action,
    Behavior,
    BehaviorProgress,
    Category,
    CategoryProgress,
    Goal,
    GoalProgress,
    PackageEnrollment,
    Trigger,
    UserCompletedAction,
    UserCompletedCustomAction,
    UserGoal,
    popular_actions,
    popular_behaviors,
    popular_goals,
    popular_categories,
)
from . permissions import (
    ContentPermissions,
    is_content_editor,
    is_package_contributor,
    permission_required,
    staff_required,
)
from . utils import num_user_selections


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
            if request.POST.get('publish', False):
                obj.publish()
                obj.save(updated_by=request.user)
                messages.success(request, "{0} has been published".format(obj))
            elif request.POST.get('decline', False):
                obj.decline()
                obj.save(updated_by=request.user)
                messages.success(request, "{0} has been declined".format(obj))
            elif request.POST.get('draft', False):
                selections = num_user_selections(obj)
                if selections > 0:
                    msg = (
                        "{0} cannot be reverted to Draft, since {1} users "
                        "have selected it in the app."
                    )
                    messages.warning(request, msg.format(obj, selections))
                    return redirect(obj.get_absolute_url())
                else:
                    obj.draft()
                    obj.save(updated_by=request.user)
                    messages.success(request, "{0} is now in Draft".format(obj))
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
        if is_content_editor(request.user):
            context['is_editor'] = True

            # Show content pending review.
            mapping = {
                'categories': Category.objects.only(*only_fields).filter,
                'goals': Goal.objects.only(*only_fields).filter,
                'behaviors': Behavior.objects.only(*only_fields).filter,
                'actions': Action.objects.only(*only_fields).filter,
            }
            for key, func in mapping.items():
                context[key] = func(state='pending-review').order_by("-updated_on")

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
        context['has_my_content'] = any([
            context['my_categories'].exists(),
            context['my_goals'].exists(),
            context['my_behaviors'].exists(),
            context['my_actions'].exists(),
        ])

        # Most popular content.
        context['popular_categories'] = popular_categories()
        context['popular_goals'] = popular_goals()
        context['popular_behaviors'] = popular_behaviors()
        context['popular_actions'] = popular_actions()

        return self.render_to_response(context)


class CategoryListView(ContentViewerMixin, ListView):
    model = Category
    context_object_name = 'categories'
    template_name = "goals/category_list.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(Count('usercategory'))
        return queryset.prefetch_related("goal_set", "goal_set__behavior_set")


class CategoryDetailView(ContentViewerMixin, DetailView):
    queryset = Category.objects.all()
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"


class CategoryCreateView(ContentEditorMixin, CreatedByView):
    model = Category
    form_class = CategoryForm
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"

    def get_initial(self, *args, **kwargs):
        """Pre-populate the value for the initial order. This can't be done
        at the class level because we want to query the value each time."""
        initial = super(CategoryCreateView, self).get_initial(*args, **kwargs)
        if 'order' not in initial:
            initial['order'] = get_max_order(Category)
        return initial

    def get_context_data(self, **kwargs):
        context = super(CategoryCreateView, self).get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


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


class CategoryUpdateView(ContentEditorMixin, ReviewableUpdateMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"

    def get_context_data(self, **kwargs):
        context = super(CategoryUpdateView, self).get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class CategoryDeleteView(ContentEditorMixin, ContentDeleteView):
    model = Category
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"
    success_url = reverse_lazy('goals:index')


class GoalListView(ContentViewerMixin, ListView):
    model = Goal
    context_object_name = 'goals'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(Count('usergoal'))
        return queryset.prefetch_related("behavior_set", "categories")


class GoalDetailView(ContentViewerMixin, DetailView):
    queryset = Goal.objects.all()
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"


class GoalCreateView(ContentAuthorMixin, CreatedByView):
    model = Goal
    form_class = GoalForm
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"

    def get_context_data(self, **kwargs):
        context = super(GoalCreateView, self).get_context_data(**kwargs)
        context['goals'] = Goal.objects.all().prefetch_related("categories")
        return context

    def form_valid(self, form):
        """Upons saving, also check if this was submitted for review."""
        result = super().form_valid(form)
        if self.request.POST.get('review', False):
            msg = ("This goal must have child behaviors that are either "
                   "published or in review before it can be reviewed.")
            messages.warning(self.request, msg)
        return result


class GoalDuplicateView(GoalCreateView):
    """Initializes the Create form with a copy of data from another object."""
    def get_initial(self, *args, **kwargs):
        initial = super(GoalDuplicateView, self).get_initial(*args, **kwargs)
        try:
            obj = self.get_object()
            initial.update({
                "title": "Copy of {0}".format(obj.title),
                "categories": obj.categories.values_list("id", flat=True),
                "description": obj.description,
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
    queryset = Trigger.objects.default().values('id', 'name', 'time', 'recurrences')
    context_object_name = 'triggers'


class TriggerDetailView(ContentEditorMixin, DetailView):
    queryset = Trigger.objects.default()
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"


class BehaviorListView(ContentViewerMixin, ListView):
    model = Behavior
    context_object_name = 'behaviors'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(Count('userbehavior'))
        return queryset.prefetch_related(
            "goals", "goals__categories", "action_set"
        )


class BehaviorDetailView(ContentViewerMixin, DetailView):
    queryset = Behavior.objects.all()
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"


class BehaviorCreateView(ContentAuthorMixin, CreatedByView):
    model = Behavior
    form_class = BehaviorForm
    slug_field = "title_slug"
    slug_url_kwarg = "title_slug"

    def get_context_data(self, **kwargs):
        context = super(BehaviorCreateView, self).get_context_data(**kwargs)
        context['behaviors'] = Behavior.objects.all()
        return context

    def form_valid(self, form):
        """Submitting for review on creation should to the appropriate state
        transition. """
        result = super().form_valid(form)
        if self.request.POST.get('review', False):
            self.object.review()  # Transition to the new state
            msg = "{0} has been submitted for review".format(self.object)
            messages.success(self.request, msg)
        self.object.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
        return result


class BehaviorDuplicateView(BehaviorCreateView):
    """Initializes the Create form with a copy of data from another object."""
    def get_initial(self, *args, **kwargs):
        initial = super(BehaviorDuplicateView, self).get_initial(*args, **kwargs)
        try:
            obj = self.get_object()
            initial.update({
                "title": "Copy of {0}".format(obj.title),
                "sequence_order": obj.sequence_order,
                "description": obj.description,
                "more_info": obj.more_info,
                "informal_list": obj.informal_list,
                "external_resoruce": obj.external_resource,
                "goals": obj.goals.values_list("id", flat=True),
                "source_link": obj.source_link,
                "source_notes": obj.source_notes,
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


class ActionListView(ContentViewerMixin, ListView):
    model = Action
    context_object_name = 'actions'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(Count('useraction'))
        return queryset.select_related(
            "behavior__title",
            'default_trigger__time',
            'default_trigger__trigger_date',
            'default_trigger__recurrences'
        )


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
    action_type = Action.CUSTOM
    trigger_date = None

    def _set_action_type(self, action_type):
        """Ensure the provided action type is valid."""
        if action_type in [at[0] for at in Action.ACTION_TYPE_CHOICES]:
            self.action_type = action_type

    def _set_trigger_date(self, date):
        if date:
            self.trigger_date = datetime.strptime(date, "%Y-%m-%d")

    def get_initial(self):
        data = self.initial.copy()
        data.update(self.form_class.INITIAL[self.action_type])
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

    def form_valid(self, form, trigger_form):
        self.object = form.save()
        default_trigger = trigger_form.save(commit=False)
        trigger_name = "Default: {0}-{1}".format(self.object, self.object.id)
        default_trigger.name = trigger_name
        default_trigger.save()
        self.object.default_trigger = default_trigger

        # If the POSTed data contains a True 'review' value, the user clicked
        # the "Submit for Review" button.
        if self.request.POST.get('review', False):
            self.object.review()  # Transition to the new state
            msg = "{0} has been submitted for review".format(self.object)
            messages.success(self.request, msg)

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
        context['action_type'] = self.action_type

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
                "external_resource": obj.external_resource,
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
        return redirect(self.get_success_url())

    def form_invalid(self, form, trigger_form):
        ctx = self.get_context_data(form=form, trigger_form=trigger_form)
        return self.render_to_response(ctx)

    def get_context_data(self, **kwargs):
        context = super(ActionUpdateView, self).get_context_data(**kwargs)
        # We also list all existing actions & link to them.
        context['actions'] = Action.objects.all().select_related("behavior__title")

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
            self.request.user in self.object.package_contributors.all()
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
        # CategoryProgress
        category_progresses = CategoryProgress.objects.filter(
            category=package.category,
            user=user
        )

        # GoalProgress
        goal_progresses = GoalProgress.objects.filter(
            usergoal__in=user_goals
        )

        # BehaviorProgress
        behavior_progresses = BehaviorProgress.objects.filter(
            user_behavior__in=user_behaviors
        )

        # UserCompletedActions
        ucas = UserCompletedAction.objects.filter(useraction__in=user_actions)

        return {
            'user_goals': user_goals,
            'user_behaviors': user_behaviors,
            'user_actions': user_actions,
            'category_progresses': category_progresses,
            'goal_progresses': goal_progresses,
            'behavior_progresses': behavior_progresses,
            'ucas': ucas,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        package = self.get_object()
        data = self.get_package_data(package)

        user_goals = data['user_goals']
        user_behaviors = data['user_behaviors']
        user_actions = data['user_actions']
        category_progresses = data['category_progresses']
        goal_progresses = data['goal_progresses']
        behavior_progresses = data['behavior_progresses']
        ucas = data['ucas']

        field = 'reported_on'
        cp_dates = category_progresses.aggregate(Min(field), Max(field))
        gp_dates = goal_progresses.aggregate(Min(field), Max(field))
        bp_dates = behavior_progresses.aggregate(Min(field), Max(field))
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
        context['category_progresses'] = category_progresses
        context['cp_dates'] = cp_dates
        context['goal_progresses'] = goal_progresses
        context['gp_dates'] = gp_dates
        context['behavior_progresses'] = behavior_progresses
        context['bp_dates'] = bp_dates
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
            self.request.user in self.category.package_contributors.all()
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
        context['app_url'] = settings.PLAY_APP_URL
        context['packages'] = PackageEnrollment.objects.filter(
            id__in=self.request.session.get("package_ids", [])
        )
        return context


@user_passes_test(is_package_contributor, login_url='/goals/')
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


@user_passes_test(staff_required, login_url='/')
def duplicate_content(request, pk, title_slug):
    category = get_object_or_404(Category, pk=pk, title_slug=title_slug)
    if request.method == "POST":
        form = TitlePrefixForm(request.POST)
        if form.is_valid():
            category = category.duplicate_content(form.cleaned_data['prefix'])
            messages.success(request, "Your content has been duplicated")
            return redirect(category.get_absolute_url())
    else:
        form = TitlePrefixForm()

    context = {
        'category': category,
        'form': form,
    }
    return render(request, 'goals/duplicate_content.html', context)


@user_passes_test(staff_required, login_url='/')
def debug_notifications(request):
    """A view to allow searching by email addresss, then listing all UserActions
    for a day, with all of the sheduled GCMNotifications for that user.

    """
    User = get_user_model()
    customactions = None
    useractions = None
    completed_useractions = None
    completed_customactions = None
    progress = None
    next_user_action = None
    today = None
    upcoming_useractions = []
    upcoming_customactions = []
    email = request.GET.get('email_address', None)

    if email is None:
        form = EmailForm()
    else:
        form = EmailForm(initial={'email_address': email})
        try:
            user = User.objects.get(email__icontains=email)
            today = local_day_range(user)
            useractions = user.useraction_set.all()
            useractions = useractions.order_by("next_trigger_date").distinct()
            completed_useractions = UserCompletedAction.objects.filter(
                user=user,
                updated_on__range=today
            )

            # Custom Actions
            customactions = user.customaction_set.all()
            customactions = customactions.order_by("next_trigger_date")
            customactions = customactions.distinct()

            completed_customactions = UserCompletedCustomAction.objects.filter(
                user=user,
                updated_on__range=today
            )

            progress = user_feed.todays_progress(user)
            next_user_action = user_feed.next_user_action(user)
            upcoming_useractions = user_feed.todays_actions(user)
            upcoming_customactions = user_feed.todays_customactions(user)
            for ua in useractions:
                ua.upcoming = ua in upcoming_useractions
            for ca in customactions:
                ca.upcoming = ca in upcoming_customactions

        except (User.DoesNotExist, User.MultipleObjectsReturned):
            messages.error(request, "Could not find that user")

    context = {
        'form': form,
        'email': email,
        'useractions': useractions,
        'customactions': customactions,
        'completed_useractions': completed_useractions,
        'completed_customactions': completed_customactions,
        'progress': progress,
        'next_user_action': next_user_action,
        'upcoming_useractions': upcoming_useractions,
        'upcoming_customactions': upcoming_customactions,
        'today': today,
    }
    return render(request, 'goals/debug_notifications.html', context)


@user_passes_test(staff_required, login_url='/')
def debug_progress(request):
    """A view to allow searching by email addresss then view and
    analyze their Category/Goal/Behavior progress data.

    """
    User = get_user_model()
    email = request.GET.get('email_address', None)
    user = None
    form = EmailForm(initial={'email_address': email})
    try:
        user = User.objects.get(email__icontains=email)
    except (User.DoesNotExist, User.MultipleObjectsReturned):
        messages.error(request, "Could not find that user")
        return redirect(reverse('debug_progress'))
    except ValueError:
        user = None

    today = timezone.now()
    days_ago = int(request.GET.get('days_ago', 30))
    from_date = today - timedelta(days=days_ago)

    # Category Progress Avg Score
    categories = Category.objects.values_list('id', 'title')
    cat_ids = [t[0] for t in categories]
    cat_labels = [t[1] for t in categories]
    cat_datasets = []
    avg_scores = []
    for cid in cat_ids:
        params = {
            'category__id': cid,
            'reported_on__range': (from_date, today),
            'user': user,
        }
        results = CategoryProgress.objects.filter(**params)
        results = results.aggregate(Avg('current_score'))
        avg_scores.append(round(results['current_score__avg'] or 0, 1))

    cat_datasets.append({
        "label": "Average Score",
        "data": avg_scores,
    })

    # Behavior Progress Avg Score
    behavior_labels = []
    behavior_datasets = []
    status_scores = []
    ap_scores = []
    for day in dates_range(days_ago):
        behavior_labels.append(day.strftime("%F"))
        params = {
            'user': user,
            'reported_on__year': day.year,
            'reported_on__month': day.month,
            'reported_on__day': day.day,
        }
        results = BehaviorProgress.objects.filter(**params)
        results = results.aggregate(Avg('status'), Avg('daily_actions_completed'))
        status_scores.append(round(results['status__avg'] or 0, 2))
        ap_scores.append(round(results['daily_actions_completed__avg'] or 0, 2))

    status_data = {'label': 'Behavior Checkin', 'data': status_scores}
    ap_data = {'label': 'Actions Completed', 'data': ap_scores}
    behavior_datasets.append((status_data, ap_data))

    # Goal Progress Scores
    goal_progress_labels = []
    goal_progress_datasets = []
    goal_progress_scores = []
    for day in dates_range(days_ago):
        goal_progress_labels.append(day.strftime("%F"))
        params = {
            'user': user,
            'reported_on__year': day.year,
            'reported_on__month': day.month,
            'reported_on__day': day.day,
        }
        results = GoalProgress.objects.filter(**params)
        results = results.aggregate(Avg('current_score'))
        goal_progress_scores.append(round(results['current_score__avg'] or 0, 2))

    goal_progress_data = {'label': 'Goal Progress', 'data': goal_progress_scores}
    goal_progress_datasets.append(goal_progress_data)

    # Goal Action Scores
    goal_actions_labels = []
    goal_actions_datasets = []
    daily = []
    weekly = []
    monthly = []
    for day in dates_range(days_ago):
        goal_actions_labels.append(day.strftime("%F"))
        params = {
            'user': user,
            'reported_on__year': day.year,
            'reported_on__month': day.month,
            'reported_on__day': day.day,
        }
        results = GoalProgress.objects.filter(**params)
        results = results.aggregate(
            Avg('daily_action_progress'),
            Avg('weekly_action_progress'),
            Avg('action_progress')
        )
        daily.append(round(results['daily_action_progress__avg'] or 0, 2))
        weekly.append(round(results['weekly_action_progress__avg'] or 0, 2))
        monthly.append(round(results['action_progress__avg'] or 0, 2))

    daily_data = {'label': 'Goal Daily Actions', 'data': daily}
    weekly_data = {'label': 'Goal Weekly Actions', 'data': weekly}
    monthly_data = {'label': 'Goal Montly Actions', 'data': monthly}
    goal_actions_datasets.append((daily_data, weekly_data, monthly_data))

    # User Completed Actions?
    uca_labels = []
    completed = []
    snoozed = []
    dismissed = []
    for day in dates_range(days_ago):
        uca_labels.append(day.strftime("%F"))
        params = {
            'user': user,
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

    context = {
        'searched_user': user,
        'form': form,
        'email': email,
        'days_ago': days_ago,
        'today': today,
        'from_date': from_date,
        'cat_labels': cat_labels,
        'cat_datasets': cat_datasets,
        'behavior_labels': behavior_labels,
        'behavior_datasets': behavior_datasets,
        'goal_progress_labels': goal_progress_labels,
        'goal_progress_datasets': goal_progress_datasets,
        'goal_actions_labels': goal_actions_labels,
        'goal_actions_datasets': goal_actions_datasets,
        'uca_labels': uca_labels,
        'uca_datasets': uca_datasets,
    }
    return render(request, 'goals/debug_progress.html', context)


@user_passes_test(staff_required, login_url='/')
def debug_progress_aggregates(request):
    today = timezone.now()
    days_ago = int(request.GET.get('days_ago', 30))
    from_date = today - timedelta(days=days_ago)

    # Category Progress Avg Score
    categories = Category.objects.values_list('id', 'title')
    cat_ids = [t[0] for t in categories]
    cat_labels = [t[1] for t in categories]
    cat_datasets = []
    avg_scores = []
    for cid in cat_ids:
        params = {
            'category__id': cid,
            'reported_on__range': (from_date, today),
        }
        results = CategoryProgress.objects.filter(**params)
        results = results.aggregate(Avg('current_score'))
        avg_scores.append(round(results['current_score__avg'] or 0, 1))

    cat_datasets.append({
        "label": "Average Score",
        "data": avg_scores,
    })

    # Behavior Progress Avg Score
    behavior_labels = []
    behavior_datasets = []
    status_scores = []
    ap_scores = []
    for day in dates_range(days_ago):
        behavior_labels.append(day.strftime("%F"))
        params = {
            'reported_on__year': day.year,
            'reported_on__month': day.month,
            'reported_on__day': day.day,
        }
        results = BehaviorProgress.objects.filter(**params)
        results = results.aggregate(Avg('status'), Avg('daily_actions_completed'))
        status_scores.append(round(results['status__avg'] or 0, 2))
        ap_scores.append(round(results['daily_actions_completed__avg'] or 0, 2))

    status_data = {'label': 'Behavior Checkin', 'data': status_scores}
    ap_data = {'label': 'Actions Completed', 'data': ap_scores}
    behavior_datasets.append((status_data, ap_data))

    # Goal Progress Scores
    goal_progress_labels = []
    goal_progress_datasets = []
    goal_progress_scores = []
    for day in dates_range(days_ago):
        goal_progress_labels.append(day.strftime("%F"))
        params = {
            'reported_on__year': day.year,
            'reported_on__month': day.month,
            'reported_on__day': day.day,
        }
        results = GoalProgress.objects.filter(**params)
        results = results.aggregate(Avg('current_score'))
        goal_progress_scores.append(round(results['current_score__avg'] or 0, 2))

    goal_progress_data = {'label': 'Goal Progress', 'data': goal_progress_scores}
    goal_progress_datasets.append(goal_progress_data)

    # Goal Actions Scores
    goal_actions_labels = []
    goal_actions_datasets = []
    daily = []
    weekly = []
    monthly = []
    for day in dates_range(days_ago):
        goal_actions_labels.append(day.strftime("%F"))
        params = {
            'reported_on__year': day.year,
            'reported_on__month': day.month,
            'reported_on__day': day.day,
        }
        results = GoalProgress.objects.filter(**params)
        results = results.aggregate(
            Avg('daily_action_progress'),
            Avg('weekly_action_progress'),
            Avg('action_progress')
        )
        daily.append(round(results['daily_action_progress__avg'] or 0, 2))
        weekly.append(round(results['weekly_action_progress__avg'] or 0, 2))
        monthly.append(round(results['action_progress__avg'] or 0, 2))

    daily_data = {'label': 'Goal Daily Actions', 'data': daily}
    weekly_data = {'label': 'Goal Weekly Actions', 'data': weekly}
    monthly_data = {'label': 'Goal Montly Actions', 'data': monthly}
    goal_actions_datasets.append((daily_data, weekly_data, monthly_data))

    # User Completed Actions?
    uca_labels = []
    completed = []
    snoozed = []
    dismissed = []
    for day in dates_range(days_ago):
        uca_labels.append(day.strftime("%F"))
        params = {
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

    context = {
        'days_ago': days_ago,
        'today': today,
        'from_date': from_date,
        'cat_labels': cat_labels,
        'cat_datasets': cat_datasets,
        'behavior_labels': behavior_labels,
        'behavior_datasets': behavior_datasets,
        'goal_progress_labels': goal_progress_labels,
        'goal_progress_datasets': goal_progress_datasets,
        'goal_actions_labels': goal_actions_labels,
        'goal_actions_datasets': goal_actions_datasets,
        'uca_labels': uca_labels,
        'uca_datasets': uca_datasets,
    }
    return render(request, 'goals/debug_progress_aggregates.html', context)


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
    custom_triggers = triggers.filter(user__isnull=False, recurrences__isnull=False)
    custom_recurrences = []
    for t in custom_triggers:
        custom_recurrences.append(t.recurrences_as_text())
    custom_recurrences = Counter(custom_recurrences)

    context = {
        'total_trigger_count': total_trigger_count,
        'custom_trigger_count': custom_trigger_count,
        'default_trigger_count': total_trigger_count - custom_trigger_count,
        'with_recurrences': with_recurrences,
        'time_and_date_only': time_and_date_only,
        'time_only': time_only,
        'date_only': date_only,
        'custom_recurrences': custom_recurrences.most_common(20),
    }
    return render(request, 'goals/report_triggers.html', context)
