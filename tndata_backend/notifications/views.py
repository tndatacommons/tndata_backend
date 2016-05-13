from collections import defaultdict
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone

from utils.datastructures import flatten

from . import queue
from .models import GCMMessage


@user_passes_test(lambda u: u.is_staff, login_url='/')
def dashboard(request):
    """A simple dashboard for enqueued GCM notifications."""
    User = get_user_model()

    # If we have specified a user, show their Queue details.
    date = request.GET.get('date', None) or None
    if date is None:
        date = timezone.now().date()
    else:
        date = datetime.strptime(date, "%Y-%m-%d").date()

    user = None
    email = request.GET.get('user', None)
    user_queues = []  # Prioritized user queue
    try:
        user = User.objects.get(email__icontains=email)
        user_queues.append(queue.UserQueue.get_data(user, date=date))
        date = date + timedelta(days=1)
        user_queues.append(queue.UserQueue.get_data(user, date=date))
    except (User.DoesNotExist, ValueError, TypeError):
        if user is not None:
            messages.warning(request, "No data found for '{}'".format(user))
    except User.MultipleObjectsReturned:
        messages.warning(request, "Multiple Users found for '{}'".format(user))

    jobs = queue.messages()  # Get the enqueued messages
    ids = [job.args[0] for job, _ in jobs]

    message_data = defaultdict(dict)
    for msg in GCMMessage.objects.filter(pk__in=ids):
        message_data[msg.id] = {
            'id': msg.id,
            'title': msg.title,
            'user_id': msg.user_id,
            'email': msg.user.email,
            'message': msg.message,
            'title': msg.title,
            'date_string': msg.deliver_on.strftime("%Y-%m-%d"),
            'queue_id': msg.queue_id,
        }

    jobs = [
        (job, scheduled_for, message_data[job.args[0]])
        for job, scheduled_for in jobs
    ]

    context = {
        'email': email,
        'jobs': jobs,
        'metrics': ['GCM Message Sent', 'GCM Message Scheduled'],
        'selected_date': date,
        'selected_user': user,
        'user_queues': user_queues,
    }
    return render(request, "notifications/index.html", context)


@user_passes_test(lambda u: u.is_staff, login_url='/')
def userqueue(request, user_id, date):
    """Return UserQueue details; i.e. the sheduled notifications/jobs for the
    user for a given date.
    """
    user = get_object_or_404(get_user_model(), pk=user_id)
    date = datetime.strptime(date, '%Y-%m-%d')
    data = queue.UserQueue.get_data(user, date)

    # massage that data a bit.
    results = {}
    for key, values in data.items():
        if 'count' in key:
            results['count'] = values
        elif 'low' in key:
            results['low'] = values
        elif 'medium' in key:
            results['medium'] = values
        elif 'high' in key:
            results['high'] = values
    results['date'] = date.strftime("%Y-%m-%d")
    results['user'] = user.get_full_name()
    return JsonResponse(results)


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
    """Cancels queued messages."""

    count = 0
    if request.method == "POST" and request.POST.get('orphaned') == 'on':
        # Sometimes we end up with orphaned jobs (e.g. a user is deleted, but
        # GCMMessage's delete signal handler doesn't fire).
        queue_ids = list(GCMMessage.objects.values_list('queue_id', flat=True))
        jobs = [job for job, _ in queue.messages() if job.id not in queue_ids]
        for job in jobs:
            job.cancel()
            count += 1
    elif request.method == "POST":
        for job, _ in queue.messages():
            job.cancel()
            count += 1

    messages.success(request, "Cancelled {} notifications.".format(count))
    return redirect("notifications:dashboard")
