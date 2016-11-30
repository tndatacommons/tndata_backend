from datetime import datetime

from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.generic import TemplateView

from .forms import ContactForm
from .models import OfficeHours

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


class ExamplesView(TemplateView):
    template_name = "officehours/mdl_examples.html"


def add_code(request):
    if request.method == "POST":
        pass
        # return redirect(program.get_absolute_url())
    else:
        # form = MembersForm()
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
    """
    Allow a user to add office hours.

    NOTE: This doesn't use any Forms because I wasted a whole day trying to
    get this form UI working with MDL; so, I just gave up and hard-coded the
    html form.

    """
    from_error = None
    to_error = None
    from_time = ''
    to_time = ''
    selected_days = []

    if request.method == "POST":
        try:
            from_time = request.POST['from_time']
            from_time = datetime.strptime(from_time, '%I:%M %p').time()
        except ValueError:
            from_time = ''
            from_error = "Enter a valid time"

        try:
            to_time = request.POST['to_time']
            to_time = datetime.strptime(to_time, '%I:%M %p').time()
        except ValueError:
            to_time = ''
            to_error = "Enter a valid time"

        for key, val in request.POST.items():
            if val == "on":
                selected_days.append(key)

        if all([from_time, to_time, selected_days]):
            OfficeHours.objects.create(
                user=request.user,
                from_time=from_time,
                to_time=to_time,
                days=selected_days
            )
            messages.success(request, "Office hours saved.")
            if request.POST.get('another') == "true":
                return redirect("officehours:add-hours")
            return redirect("/officehours/add-hours/")  # TODO: what's next
        else:
            messages.error(request, "Unable to save your office hours.")

    context = {
        'from_time': from_time,
        'from_error': from_error,
        'to_error': to_error,
        'to_time': to_time,
        'selected_days': selected_days,
        'day_choices': [
            'Sunday', 'Monday', 'Tuesday', 'Wednesday',
            'Thursday', 'Friday', 'Saturday',
        ]
    }
    return render(request, 'officehours/add_hours.html', context)
