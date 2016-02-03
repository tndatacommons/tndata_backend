from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from redis_metrics import metric
import django_rq

from utils.slack import post_private_message


def get_scheduler(queue='default'):
    return django_rq.get_scheduler('default')


# XXX: This Module-level scheduler is our interface to putting messages
#      on the notifications task queue.
scheduler = get_scheduler()


def send(message_id):
    """Given an ID for a GCMMessage object, send the message via GCM."""
    msg = "Trying to send GCMMessage id = {} from {}"
    msg = msg.format(message_id, settings.SITE_URL)
    post_private_message("bkmontgomery", msg)

    try:
        from . models import GCMMessage
        msg = GCMMessage.objects.get(pk=message_id)
        msg.send()  # NOTE: sets a metric on successful sends.
        post_private_message("bkmontgomery", "...done!")
    except Exception as e:
        msg = "FAILED: {}".format(e)
        post_private_message("bkmontgomery", msg)


def enqueue(message, threshold=24):
    """Given a GCMMessage object, add it to the queue of messages to be sent.

    TODO:
        - priorities
        - thresholds: max number of daily messages per user

    """

    job = None
    now = timezone.now()
    threshold = now + timedelta(hours=threshold)

    # Only queue up messages for the next 24 hours
    if now < message.deliver_on and message.deliver_on < threshold:
        job = scheduler.enqueue_at(message.deliver_on, send, message.id)

        # Save the job ID on the GCMMessage, so if it gets re-enqueued we
        # can cancel the original?
        message.queue_id = job.id
        message.save()

        # Record a metric so we can see queued vs sent?
        metric('GCM Message Scheduled', category='Notifications')

    return job


def messages():
    """Return a list of jobs that are scheduled with their scheduled times.

    Returned data is a list of (Job, datetime) tuples.

    """
    return scheduler.get_jobs(with_times=True)
