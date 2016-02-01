from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from . import queue


@user_passes_test(lambda u: u.is_staff, login_url='/')
def dashboard(request):
    """A simple dashboard for enqueued GCM notifications."""

    jobs = queue.messages()  # Get the enqueued messages

    context = {'jobs': jobs}
    return render(request, "notifications/index.html", context)

