from datetime import datetime

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import TemplateView

from .forms import ContactForm
from .models import Course, OfficeHours

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


class ExamplesView(TemplateView):
    template_name = "officehours/mdl_examples.html"


def index(request):
    if (
        request.user.is_authenticated() and
        (request.user.officehours_set.exists() or
         request.user.teaching.exists() or
         request.user.course_set.exists())
    ):
        return redirect("officehours:schedule")

    return render(request, 'officehours/index.html', {})



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
            return redirect("officehours:add-course")
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


def add_course(request):
    """
    Allow a user to add office hours.

    NOTE: This doesn't use any Forms because I wasted a whole day trying to
    get this form UI working with MDL; so, I just gave up and hard-coded the
    html form.

    """
    coursetime = ''
    coursetime_error = None
    coursename = ''
    coursename_error = ''
    location = ''
    location_error = ''
    selected_days = []

    if request.method == "POST":
        coursename = request.POST['coursename']
        if not coursename:
            coursename_error = "Course name is required"
        location = request.POST['coursename']
        if not location:
            location_error = "Location is required"

        try:
            coursetime = request.POST['coursetime']
            coursetime = datetime.strptime(coursetime, '%I:%M %p').time()
        except ValueError:
            coursetime = ''
            coursetime = "Enter a valid time"

        for key, val in request.POST.items():
            if val == "on":
                selected_days.append(key)

        if all([coursename, coursetime, location, selected_days]):
            course = Course.objects.create(
                user=request.user,
                name=coursename,
                start_time=coursetime,
                location=location,
                days=selected_days
            )
            messages.success(request, "Course info saved.")
            if request.POST.get('another') == "true":
                return redirect("officehours:add-course")
            return redirect(course.get_share_url())
        else:
            messages.error(request, "Unable to save your course.")

    context = {
        'coursename': coursename,
        'coursename_error': coursename_error,
        'coursetime': coursetime,
        'coursetime_error': coursetime_error,
        'location': location,
        'location_error': location_error,
        'selected_days': selected_days,
        'day_choices': [
            'Sunday', 'Monday', 'Tuesday', 'Wednesday',
            'Thursday', 'Friday', 'Saturday',
        ]
    }
    return render(request, 'officehours/add_course.html', context)


def share_course(request, pk):
    """Display the course's share code"""
    context = {
        'course': get_object_or_404(Course, pk=pk)
    }
    return render(request, 'officehours/share_course.html', context)


def course_details(request, pk):
    """Display course details"""
    context = {
        'course': get_object_or_404(Course, pk=pk)
    }
    return render(request, 'officehours/course_details.html', context)


def schedule(request):
    """List courses in which the user is a student / teacher."""

    student_schedule = request.user.course_set.all()
    teaching_schedule = request.user.teaching.all()
    office_hours = request.user.officehours_set.all()

    context = {
        'student_schedule': student_schedule,
        'teaching_schedule': request.user.teaching.all(),
        'office_hours': office_hours,
        'is_student': student_schedule.exists(),
        'is_teacher': teaching_schedule.exists() or office_hours.exists()
    }
    return render(request, 'officehours/schedule.html', context)
