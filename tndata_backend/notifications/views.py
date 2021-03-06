from collections import defaultdict
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone

from . import queue
from .forms import GCMMessageForm
from .models import GCMMessage


@login_required
def send_message(request):
    """A quick & easy way to send test notifications."""
    if request.method == "POST":
        form = GCMMessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.user = request.user
            msg.deliver_on = timezone.now()
            msg.priority = GCMMessage.HIGH
            msg.save()
            msg.send()
            messages.success(request, "Your notification has been sent")
            return redirect(reverse("notifications:view", args=[msg.id]))
    else:
        form = GCMMessageForm()

    context = {
        'form': form,
    }
    return render(request, 'notifications/send_message.html', context)


@login_required
def view_message(request, message_id):
    msg = get_object_or_404(GCMMessage, pk=message_id)
    return render(request, 'notifications/view_message.html', {'message': msg})


@user_passes_test(lambda u: u.is_staff, login_url='/')
def dashboard(request):
    """A simple dashboard for enqueued GCM notifications."""
    devices = None
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
        devices = user.gcmdevice_set.count()

        user_queues.append(queue.UserQueue.get_data(user, date=date))
        date = date + timedelta(days=1)
        user_queues.append(queue.UserQueue.get_data(user, date=date))
    except (User.DoesNotExist, ValueError, TypeError):
        if user is not None:
            messages.warning(request, "No data found for '{}'".format(user))
    except User.MultipleObjectsReturned:
        messages.warning(request, "Multiple Users found for '{}'".format(user))

    if user:
        # Get all the enqueued jobs, & keep a list of the Job.ID values.
        jobs = queue.messages()
        job_ids = [job.args[0] for job, _ in jobs]

        # Build a dict of the user's message data matching those Jobs.
        message_data = defaultdict(dict)
        for msg in user.gcmmessage_set.filter(pk__in=job_ids):
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

        # Restrict the list of jobs to those intended for the given user.
        jobs = [
            (job, scheduled_for, message_data[job.args[0]])
            for job, scheduled_for in jobs if job.args[0] in message_data
        ]
    else:
        jobs = []

    context = {
        'devices': devices,
        'email': email,
        'num_jobs': queue.get_scheduler().count(),
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
