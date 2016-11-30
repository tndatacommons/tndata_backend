from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.generic import TemplateView

from .forms import ContactForm, OfficeHoursForm

# index
# - welcome (if no courses)
# - course list
#
# choose role (student / teacher)
# - student
# -- enter code (to index)
# - teacher
# -- update contact info
# -- office hours -> repeat
# -- add course -> repeat
# -- share


class IndexView(TemplateView):
    template_name = "officehours/index.html"

    # def get_context_data(self, **kwargs):
        # context = super().get_context_data(**kwargs)
        # messages.warning(self.request, "WARN. This is a Warning.")
        # messages.success(self.request, "SUCCESS. This is a success message.")
        # return context


class ExamplesView(TemplateView):
    template_name = "officehours/mdl_examples.html"


def add_code(request):
    if request.method == "POST":
        pass
        #return redirect(program.get_absolute_url())
    else:
        #form = MembersForm()
        pass

    context = {}
    return render(request, 'officehours/add_code.html', context)


def contact_info(request):
    if request.method == "POST":
        form = ContactForm(request.POST)

        if form.is_valid():
            request.user.userprofile.phone = form.cleaned_data['phone']
            request.user.userprofile.save()
            request.user.email = form.cleaned_data['email']

            parts = form.cleaned_data['your_name'].split()
            first, last = parts[:-1], parts[1]
            request.user.first_name = " ".join(first)
            request.user.last_name = last
            request.user.save()

            messages.success(request, "Contact info saved.")
            return redirect("officehours:add-hours")
        else:
            messages.error(request, "Unable to save your info.")
    else:
        initial = {
            'your_name': request.user.get_full_name(),
            'email': request.user.email,
            'phone': request.user.userprofile.phone,
        }
        form = ContactForm(initial=initial)

    context = {'form': form}
    return render(request, 'officehours/contact_info.html', context)


def add_hours(request):
    if request.method == "POST":
        form = OfficeHoursForm(request.POST)

        if form.is_valid():
            hours = form.save(commit=False)
            hours.user = request.user
            hours.save()

            messages.success(request, "Office hours saved.")
            # TODO: next / add another.
            return redirect("/")
        else:
            messages.error(request, "Unable to save your office hours.")
    else:
        form = OfficeHoursForm()

    context = {'form': form}
    return render(request, 'officehours/add_hours.html', context)
