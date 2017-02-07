from collections import Counter
from datetime import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import login as login_user
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.generic import TemplateView

from chat.models import ChatMessage
from userprofile.models import UserProfile
from notifications.sms import format_numbers
from userprofile.forms import UserForm
from utils.forms import SetNewPasswordForm
from utils.user_utils import username_hash, get_client_ip

from .forms import ContactForm
from .models import Course, OfficeHours


class AboutView(TemplateView):
    template_name = 'officehours/about.html'


class HelpView(TemplateView):
    template_name = 'officehours/help.html'


class ContactView(TemplateView):
    template_name = 'officehours/contact.html'


def index(request):
    user = request.user

    # Are we logged in?
    if user.is_authenticated():
        # if so, have we already added a course or any other data?
        if (
            user.officehours_set.exists() or
            user.teaching.exists() or
            user.course_set.exists()
        ):
            return redirect("officehours:schedule")

        # Otherwise, show the index (which is a getting-started page)
        return render(request, 'officehours/index.html', {})

    # Otherwise show the google auth login.
    return redirect("officehours:login")


def login(request):
    if request.user.is_authenticated():
        return redirect("officehours:schedule")

    if request.method == "POST" and request.is_ajax():
        email = request.POST.get('email')
        token = request.POST.get('token')
        user = authenticate(email=email, token=token)
        if user is None:
            return JsonResponse({'error': "User not found"}, status=400)
        else:
            login_user(request, user)
            return JsonResponse({'user_id': user.id}, status=200)

    return render(request, 'officehours/login.html', {})


@login_required
def add_code(request):
    if request.method == "POST":
        next_url = request.POST.get('next') or 'officehours:schedule'
        code = "{}".format(request.POST['code']).strip().upper()
        try:
            course = Course.objects.get(code=code)
            course.students.add(request.user)
            messages.success(request, "Course added to your schedule.")
            return redirect(next_url)
        except Course.DoesNotExist:
            messages.error(request, "Could not find that course.")
            return redirect('officehours:add-code')

    context = {
        'next_url': request.GET.get('next', '')
    }
    return render(request, 'officehours/add_code.html', context)


@login_required
def phone_number(request):
    error = None
    phone = request.user.userprofile.phone
    if request.method == "POST" and 'phone' in request.POST:
        try:
            phone = request.POST['phone']
            if format_numbers([phone]):
                request.user.userprofile.phone = phone
                request.user.userprofile.save()
                messages.success(request, "Phone number updated.")
                return redirect('officehours:schedule')
            error = "Sorry, that doesn't look like a phone number."
        except (UserProfile.DoesNotExist, IndexError):
            messages.error(request, "Could not save your information.")
            return redirect('officehours:index')

    context = {
        'phone': phone,
        'error': error,
    }
    return render(request, 'officehours/phone_number.html', context)


@login_required
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


@login_required
def add_hours(request):
    """
    Allow a user to add office hours.

    NOTE: This doesn't use any Forms because I wasted a whole day trying to
    get this form UI working with MDL; so, I just gave up and hard-coded the
    html form.

    """
    selected_days = []
    results = None

    if request.method == "POST":
        # NEED:
        #
        # { DAY: [{from: time, to: time}, ... ] }
        # ------------------------------------------------
        selected_days = [
            k for k, v in request.POST.dict().items() if v == 'on'
        ]
        results = {day: [] for day in selected_days}
        for day in selected_days:
            from_key = "from_time-{}".format(day.lower())
            to_key = "to_time-{}".format(day.lower())

            from_times = request.POST.getlist(from_key)
            to_times = request.POST.getlist(to_key)
            # zip returns tuples, we need lists to convert to JSON
            results[day] = [
                {"from": from_time, "to": to_time}
                for from_time, to_time in list(zip(from_times, to_times))
            ]
        if results:
            OfficeHours.objects.create(user=request.user, schedule=results)
            messages.success(request, "Office hours saved.")
            if request.POST.get('another') == "true":
                return redirect("officehours:add-hours")
            return redirect("officehours:add-course")
        else:
            messages.error(request, "Unable to save your office hours.")

    context = {
        'results': results,
        'day_choices': [
            'Sunday', 'Monday', 'Tuesday', 'Wednesday',
            'Thursday', 'Friday', 'Saturday',
        ]
    }
    return render(request, 'officehours/add_hours.html', context)


@login_required
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
            coursetime_error = 'Enter a valid time'

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


@login_required
def delete_course(request, pk):
    """
    Allow an INSTRUCTOR (course owner) to delete a course (with confirmation)

    """
    course = get_object_or_404(Course, pk=pk, user=request.user)

    if request.method == "POST" and bool(request.POST.get('confirm', False)):
        course_name = course.name
        course.delete()
        messages.success(request, "{} was deleted.".format(course_name))
        return redirect("officehours:schedule")

    context = {
        'course': course,
    }
    return render(request, 'officehours/delete_course.html', context)


@login_required
def share_course(request, pk):
    """Display the course's share code"""
    context = {
        'course': get_object_or_404(Course, pk=pk)
    }
    return render(request, 'officehours/share_course.html', context)


@login_required
def course_details(request, pk):
    """Display course details"""
    context = {
        'course': get_object_or_404(Course, pk=pk)
    }
    return render(request, 'officehours/course_details.html', context)


@login_required
def officehours_details(request, pk):
    """Display OfficeHours details"""
    context = {
        'hours': get_object_or_404(OfficeHours, pk=pk)
    }
    return render(request, 'officehours/officehours_details.html', context)


@login_required
def delete_officehours(request, pk):
    """
    Allow an INSTRUCTOR (officehours owner) to delete a officehours (with confirmation)

    """
    officehours = get_object_or_404(OfficeHours, pk=pk, user=request.user)

    if request.method == "POST" and bool(request.POST.get('confirm', False)):
        officehours.delete()
        messages.success(request, "Office Hours were deleted.")
        return redirect("officehours:schedule")

    context = {'hours': officehours}
    return render(request, 'officehours/delete_officehours.html', context)


@login_required
def schedule(request):
    """List courses in which the user is a student / teacher."""

    # Get unread messages for the user, then count the number from each sender
    chat_data = ChatMessage.objects.to_user(request.user).filter(read=False)
    _fields = ('user__id', 'user__first_name', 'user__last_name')
    chat_data = dict(Counter(chat_data.values_list(*_fields)))

    student_schedule = request.user.course_set.all()
    teaching_schedule = request.user.teaching.all()
    office_hours = OfficeHours.objects.current().filter(user=request.user)

    context = {
        'student_schedule': student_schedule,
        'teaching_schedule': request.user.teaching.all(),
        'office_hours': office_hours,
        'is_student': student_schedule.exists(),
        'is_teacher': teaching_schedule.exists() or office_hours.exists(),
        'chat_data': chat_data,
    }
    return render(request, 'officehours/schedule.html', context)


def create_account(request):
    """Yet another way to create an account."""
    if request.method == "POST":
        form = UserForm(request.POST)
        password_form = SetNewPasswordForm(request.POST, prefix="pw")
        if form.is_valid() and password_form.is_valid():
            User = get_user_model()
            email = form.cleaned_data['email'].strip().lower()

            try:
                # Ensure the email isn't already tied to an account
                user = User.objects.get(email__iexact=email)
                messages.info(request, "It looks like you already have an "
                                       "account! Log in to continue.")
                return redirect("officehours:login")
            except User.DoesNotExist:
                # Create & activate the account
                # XXX This is a hack to keep these users from getting the
                # XXX `selected_by_default` content from the `goals` app.
                # XXX We *must* set this before we craete the user, hence the
                # XXX use of the email in the key.
                _key = "omit-default-selections-{}".format(slugify(email))
                cache.set(_key, True, 30)

                user = form.save(commit=False)
                user.is_active = True
                user.username = username_hash(email)
                user.set_password(password_form.cleaned_data['password'])
                user.save()

                # Set their IP address.
                user.userprofile.ip_address = get_client_ip(request)
                user.userprofile.save()

                user = authenticate(
                    email=email,
                    password=password_form.cleaned_data['password']
                )
                login_user(request, user)
                return redirect("officehours:index")
        else:
            messages.error(request, "We could not process your request. "
                                    "Please see the details, below.")
    else:
        password_form = SetNewPasswordForm(prefix='pw')
        form = UserForm()

    context = {
        'form': form,
        'password_form': password_form,
    }
    return render(request, "officehours/create_account.html", context)
