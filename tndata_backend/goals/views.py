from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.forms.models import modelformset_factory
from django.shortcuts import redirect, render
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from . forms import CSVUploadForm, InterestGroupSelectionForm
from . models import Action, Category, Interest, InterestGroup
from . utils import get_max_order


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


class CategoryListView(ListView):
    model = Category
    context_object_name = 'categories'
    template_name = "goals/index.html"


class CategoryDetailView(DetailView):
    queryset = Category.objects.all()
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"


class CategoryCreateView(CreateView):
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
        if 'formset' not in kwargs:
            context['formset'] = self.get_interestgroup_formset()
        return context

    def get_interestgroup_formset(self, post_data=None):
        InterestGroupFormset = modelformset_factory(
            InterestGroup,
            fields=('name', ),
            extra=6
        )
        if post_data:
            formset = InterestGroupFormset(post_data, prefix="ig")
        else:
            formset = InterestGroupFormset(
                queryset=InterestGroup.objects.none(),
                prefix="ig"
            )
        return formset

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        formset = self.get_interestgroup_formset(request.POST)
        if form.is_valid() and formset.is_valid():
            return self.form_valid(form, formset)
        else:
            return self.form_invalid(form, formset)

    def form_invalid(self, form, formset=None):
        context = self.get_context_data(form=form, formset=formset)
        return self.render_to_response(context)

    def form_valid(self, form, formset):
        self.object = form.save()
        for instance in formset.save(commit=False):
            instance.category = self.object
            instance.save()
        formset.save_m2m()
        return super(CategoryCreateView, self).form_valid(form)


class CategoryUpdateView(UpdateView):
    model = Category
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
    fields = ['order', 'name', 'description', 'icon', 'notes']

    def get_context_data(self, **kwargs):
        context = super(CategoryUpdateView, self).get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        if 'formset' not in kwargs:
            context['formset'] = self.get_interestgroup_formset()
        return context

    def get_interestgroup_formset(self, post_data=None):
        InterestGroupFormset = modelformset_factory(
            InterestGroup,
            fields=('name', ),
            extra=3
        )
        if post_data:
            formset = InterestGroupFormset(post_data, prefix="ig")
        else:
            formset = InterestGroupFormset(queryset=self.object.groups, prefix="ig")
        return formset

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        formset = self.get_interestgroup_formset(request.POST)
        if form.is_valid() and formset.is_valid():
            return self.form_valid(form, formset)
        else:
            return self.form_invalid(form, formset)

    def form_invalid(self, form, formset=None):
        context = self.get_context_data(form=form, formset=formset)
        return self.render_to_response(context)

    def form_valid(self, form, formset):
        self.object = form.save()
        for instance in formset.save(commit=False):
            instance.category = self.object
            instance.save()
        formset.save_m2m()
        return super(CategoryUpdateView, self).form_valid(form)


class CategoryDeleteView(DeleteView):
    model = Category
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
    success_url = reverse_lazy('goals:index')


class InterestListView(ListView):
    model = Interest
    context_object_name = 'interests'


class InterestDetailView(DetailView):
    queryset = Interest.objects.all()
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"


class InterestCreateView(CreateView):
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


class InterestUpdateView(UpdateView):
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


class InterestDeleteView(DeleteView):
    model = Interest
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
    success_url = reverse_lazy('goals:index')


class InterestGroupListView(ListView):
    model = InterestGroup
    context_object_name = 'interestgroups'


class InterestGroupDetailView(DetailView):
    queryset = InterestGroup.objects.all()
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"


class InterestGroupCreateView(CreateView):
    model = InterestGroup
    fields = ['category', 'interests', 'name']

    def get_context_data(self, **kwargs):
        context = super(InterestGroupCreateView, self).get_context_data(**kwargs)
        context['interestgroups'] = InterestGroup.objects.all()
        return context


class InterestGroupUpdateView(UpdateView):
    model = InterestGroup
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
    fields = ['category', 'interests', 'name']

    def get_context_data(self, **kwargs):
        context = super(InterestGroupUpdateView, self).get_context_data(**kwargs)
        context['interestgroups'] = InterestGroup.objects.all()
        return context


class InterestGroupDeleteView(DeleteView):
    model = InterestGroup
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
    success_url = reverse_lazy('goals:index')


class ActionListView(ListView):
    model = Action
    context_object_name = 'actions'


class ActionDetailView(DetailView):
    queryset = Action.objects.all()
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"


class ActionCreateView(CreateView):
    model = Action
    fields = [
        'order', 'name', 'summary', 'description', 'interests',
        'default_reminder_time', 'default_reminder_frequency',
        'icon', 'notes', 'source_name', 'source_link',
    ]

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


class ActionUpdateView(UpdateView):
    model = Action
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
    fields = [
        'order', 'name', 'summary', 'description', 'interests',
        'default_reminder_time', 'default_reminder_frequency',
        'icon', 'notes', 'source_name', 'source_link',
    ]

    def get_context_data(self, **kwargs):
        context = super(ActionUpdateView, self).get_context_data(**kwargs)
        context['actions'] = Action.objects.all()
        return context


class ActionDeleteView(DeleteView):
    model = Action
    slug_field = "name_slug"
    slug_url_kwarg = "name_slug"
    success_url = reverse_lazy('goals:index')
