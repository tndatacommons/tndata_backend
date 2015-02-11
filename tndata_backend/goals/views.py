from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse_lazy
from django.forms.models import modelformset_factory
from django.shortcuts import redirect, render
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from . forms import ActionForm, CSVUploadForm, InterestGroupSelectionForm
from . models import Action, Category, Interest, InterestGroup
from . utils import get_max_order


def superuser_required(user):
    """Verifies that a user is authenticated and a super user."""
    return user.is_authenticated() and user.is_superuser


class SuperuserRequiredMixin(object):
    """A Mixin that requires the user to be a superuser in order to access
    the view.

    NOTE: Eventually we'll want to have more granular permissions, here. We
    probably need a group or object-level permissions and check for those
    instead (namely, once we have more than just our group editing content)
    """
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(SuperuserRequiredMixin, cls).as_view(**initkwargs)
        dec = user_passes_test(superuser_required, login_url=settings.LOGIN_URL)
        return dec(view)


@user_passes_test(superuser_required, login_url='/')
def upload_csv(request):
    """Allow a user to upload a CSV file to populate our data backend."""
    if request.method == "POST":
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'CSV File uploaded, successfully.')
                return redirect("goals:index")
            except CSVUploadForm.InvalidFormat as e:
                messages.error(
                    request, "The uploaded file could not be "
                    "processed. Please check the format and try again: "
                    " {0}".format(e)
                )
        else:
            messages.warning(
                request, "This form didn't validate. Please try again."
            )
    else:
        form = CSVUploadForm()

    context = {'form': form}
    return render(request, 'goals/upload_csv.html', context)


class IndexView(SuperuserRequiredMixin, TemplateView):
    template_name = "goals/index.html"


class CategoryListView(SuperuserRequiredMixin, ListView):
    model = Category
    context_object_name = 'categories'
    template_name = "goals/category_list.html"


class CategoryDetailView(SuperuserRequiredMixin, DetailView):
    queryset = Category.objects.all()
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"


class CategoryCreateView(SuperuserRequiredMixin, CreateView):
    model = Category
    fields = ['order', 'name', 'description', 'icon', 'notes']

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


class CategoryUpdateView(SuperuserRequiredMixin, UpdateView):
    model = Category
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
    fields = ['order', 'name', 'description', 'icon', 'notes']

    def get_context_data(self, **kwargs):
        context = super(CategoryUpdateView, self).get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class CategoryDeleteView(SuperuserRequiredMixin, DeleteView):
    model = Category
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
    success_url = reverse_lazy('goals:index')


class InterestListView(SuperuserRequiredMixin, ListView):
    model = Interest
    context_object_name = 'interests'


class InterestDetailView(SuperuserRequiredMixin, DetailView):
    queryset = Interest.objects.all()
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"


class InterestCreateView(SuperuserRequiredMixin, CreateView):
    model = Interest
    fields = [
        'order', 'name', 'description', 'notes', 'source_name', 'source_link'
    ]

    def get_initial(self, *args, **kwargs):
        """Pre-populate the value for the initial order. This can't be done
        at the class level because we want to query the value each time."""
        initial = super(InterestCreateView, self).get_initial(*args, **kwargs)
        if 'order' not in initial:
            initial['order'] = get_max_order(Interest)
        return initial

    def get_interestgroup_form(self, post_data=None):
        if post_data:
            form = InterestGroupSelectionForm(post_data, prefix="ig")
        else:
            form = InterestGroupSelectionForm(prefix="ig")
        return form

    def get_context_data(self, **kwargs):
        context = super(InterestCreateView, self).get_context_data(**kwargs)
        context['interests'] = Interest.objects.all()
        if 'ig_form' not in kwargs:
            context['ig_form'] = self.get_interestgroup_form()
        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        ig_form = self.get_interestgroup_form(request.POST)
        if form.is_valid() and ig_form.is_valid():
            return self.form_valid(form, ig_form)
        else:
            return self.form_invalid(form, ig_form)

    def form_invalid(self, form, ig_form=None):
        context = self.get_context_data(form=form, ig_form=ig_form)
        return self.render_to_response(context)

    def form_valid(self, form, ig_form):
        self.object = form.save()
        for ig in ig_form.cleaned_data['add_to_groups']:
            ig.interests.add(self.object)
        return super(InterestCreateView, self).form_valid(form)


class InterestUpdateView(SuperuserRequiredMixin, UpdateView):
    model = Interest
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
    fields = [
        'order', 'name', 'description', 'notes', 'source_name', 'source_link'
    ]

    def get_interestgroup_form(self, post_data=None):
        if post_data:
            form = InterestGroupSelectionForm(post_data, prefix="ig")
        else:
            form = InterestGroupSelectionForm(initial=self.object.groups, prefix="ig")
        return form

    def get_context_data(self, **kwargs):
        context = super(InterestUpdateView, self).get_context_data(**kwargs)
        context['interests'] = Interest.objects.all()
        if 'ig_form' not in kwargs:
            context['ig_form'] = self.get_interestgroup_form()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        ig_form = self.get_interestgroup_form(request.POST)
        if form.is_valid() and ig_form.is_valid():
            return self.form_valid(form, ig_form)
        else:
            return self.form_invalid(form, ig_form)

    def form_invalid(self, form, ig_form=None):
        context = self.get_context_data(form=form, ig_form=ig_form)
        return self.render_to_response(context)

    def form_valid(self, form, ig_form):
        self.object = form.save()
        self.object.remove_from_interestgroups()  # Remove all existing groups.
        for ig in ig_form.cleaned_data['add_to_groups']:
            ig.interests.add(self.object)
        return super(InterestUpdateView, self).form_valid(form)


class InterestDeleteView(SuperuserRequiredMixin, DeleteView):
    model = Interest
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
    success_url = reverse_lazy('goals:index')


class InterestGroupListView(SuperuserRequiredMixin, ListView):
    model = InterestGroup
    context_object_name = 'interestgroups'


class InterestGroupDetailView(SuperuserRequiredMixin, DetailView):
    queryset = InterestGroup.objects.all()
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"


class InterestGroupCreateView(SuperuserRequiredMixin, CreateView):
    model = InterestGroup
    fields = ['category', 'interests', 'name']

    def get_context_data(self, **kwargs):
        context = super(InterestGroupCreateView, self).get_context_data(**kwargs)
        context['interestgroups'] = InterestGroup.objects.all()
        return context


class InterestGroupUpdateView(SuperuserRequiredMixin, UpdateView):
    model = InterestGroup
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
    fields = ['category', 'interests', 'name']

    def get_context_data(self, **kwargs):
        context = super(InterestGroupUpdateView, self).get_context_data(**kwargs)
        context['interestgroups'] = InterestGroup.objects.all()
        return context


class InterestGroupDeleteView(SuperuserRequiredMixin, DeleteView):
    model = InterestGroup
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
    success_url = reverse_lazy('goals:index')


class ActionListView(SuperuserRequiredMixin, ListView):
    model = Action
    context_object_name = 'actions'


class ActionDetailView(SuperuserRequiredMixin, DetailView):
    queryset = Action.objects.all()
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"


class ActionCreateView(SuperuserRequiredMixin, CreateView):
    model = Action
    form_class = ActionForm

    def get_initial(self, *args, **kwargs):
        """Pre-populate the value for the initial order. This can't be done
        at the class level because we want to query the value each time."""
        initial = super(ActionCreateView, self).get_initial(*args, **kwargs)
        if 'order' not in initial:
            initial['order'] = get_max_order(Action)
        return initial

    def get_context_data(self, **kwargs):
        context = super(ActionCreateView, self).get_context_data(**kwargs)
        context['actions'] = Action.objects.all()
        return context


class ActionUpdateView(SuperuserRequiredMixin, UpdateView):
    model = Action
    form_class = ActionForm
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"

    def get_context_data(self, **kwargs):
        context = super(ActionUpdateView, self).get_context_data(**kwargs)
        context['actions'] = Action.objects.all()
        return context


class ActionDeleteView(SuperuserRequiredMixin, DeleteView):
    model = Action
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
    success_url = reverse_lazy('goals:index')
