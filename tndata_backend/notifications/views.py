from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render

from . import queue
from .models import GCMMessage


@user_passes_test(lambda u: u.is_staff, login_url='/')
def dashboard(request):
    """A simple dashboard for enqueued GCM notifications."""

    jobs = queue.messages()  # Get the enqueued messages
    ids = [job.args[0] for job, _ in jobs]

    message_data = {}
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

    jobs = (
        (job, scheduled_for, message_data[job.args[0]])
        for job, scheduled_for in jobs
    )
    context = {
        'jobs': jobs,
        'metrics': ['GCM Message Sent', 'GCM Message Scheduled', ]
    }
    return render(request, "notifications/index.html", context)
