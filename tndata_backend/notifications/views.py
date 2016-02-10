from collections import defaultdict

from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.shortcuts import render, redirect

from . import queue
from .models import GCMMessage


@user_passes_test(lambda u: u.is_staff, login_url='/')
def dashboard(request):
    """A simple dashboard for enqueued GCM notifications."""

    jobs = queue.messages()  # Get the enqueued messages
    ids = [job.args[0] for job, _ in jobs]

    message_data = defaultdict(dict)
    fields = ['id', 'title', 'user__email', 'message']
    messages = GCMMessage.objects.filter(pk__in=ids).values_list(*fields)
    for msg in messages:
        mid, title, email, message = msg
        message_data[mid] = {
            'id': mid,
            'title': title,
            'email': email,
            'message': message,
        }

    jobs = [
        (job, scheduled_for, message_data[job.args[0]])
        for job, scheduled_for in jobs
    ]
    context = {
        'jobs': jobs,
        'metrics': ['GCM Message Sent', 'GCM Message Scheduled', ]
    }
    return render(request, "notifications/index.html", context)


@user_passes_test(lambda u: u.is_staff, login_url='/')
def cancel_job(request):
    """Look for an enqueued job with the given ID and cancel it."""
    job_id = request.POST.get('job_id', None)
    if request.method == "POST" and job_id:
        for job, _ in queue.messages():
            if job.id == job_id:
                job.cancel()
                messages.success(request, "That notification has been cancelled")
                break
    return redirect("notifications:dashboard")


@user_passes_test(lambda u: u.is_staff, login_url='/')
def cancel_all_jobs(request):
    """Cancels all queued messages."""
    if request.method == "POST":
        count = 0
        for job, _ in queue.messages():
            job.cancel()
            count += 1
        messages.success(request, "Cancelled {} notifications.".format(count))
    return redirect("notifications:dashboard")
