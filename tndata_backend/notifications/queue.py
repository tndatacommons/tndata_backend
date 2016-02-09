from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from redis_metrics import metric
import django_rq

from utils.slack import post_private_message


def get_scheduler(queue='default'):
    return django_rq.get_scheduler('default')


# NOTE: This Module-level scheduler is our interface to putting messages
#       on the notifications task queue.
scheduler = get_scheduler()


def send(message_id):
    """Given an ID for a GCMMessage object, send the message via GCM."""

    try:
        from . models import GCMMessage
        msg = GCMMessage.objects.get(pk=message_id)

        log = "Trying to send GCMMessage id = {} from {} to {}"
        log = log.format(message_id, settings.SITE_URL, msg.user.email)
        post_private_message("bkmontgomery", log)

        msg.send()  # NOTE: sets a metric on successful sends.

        post_private_message("bkmontgomery", "...done!")
    except Exception as e:
        args = (e, settings.SITE_URL, message_id)
        log = "FAILED: {} on {} for id = {}".format(*args)
        post_private_message("bkmontgomery", log)


def enqueue(message, threshold=24):
    """Given a GCMMessage object, add it to the queue of messages to be sent.

    TODO: Include support for:

    - priorities
    - thresholds: max number of daily messages per user

    """

    job = None
    now = timezone.now()
    threshold = now + timedelta(hours=threshold)

    # Only queue up messages for the next 24 hours
    if now < message.deliver_on and message.deliver_on < threshold:

        # WANT:
        job = UserQueue(message).add()
        # OR
        # job = UserQueue(message).add("high")

        # ------------ deprecate the below -----------------------------
        job = scheduler.enqueue_at(message.deliver_on, send, message.id)
        # --------------------------------------------------------------

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


def cancel(queue_id):
    """Given a queue id, look up the corresponding job and cancel it. """
    if queue_id:
        jobs = (job for job, _ in messages() if job.id == queue_id)
        for job in jobs:
            job.cancel()


# -------------------------------
# TODO: PRIORITIES & Daily limits
# -------------------------------
# Idea: Use redis to keep a count of messages that are in the queue. All these
# keys should expire after 24 hours (maybe)?
#
# Keep a string to count number of daily messages scheduled / sent.
#
# e.g. SET  user:ID:2016-02-04  4 -- count for the day
#
# Keep a set per user per day of high/low priority messages?
#
# e.g: SADD user:ID:2016-02-04:high  ID1, ID2, ID3  -- high-priority messages
#      SADD user:ID:2016-02-04:low   ID4            -- low-priority messages
#
# - could use ZADD (sorted sets) for messages, to keep order, using delivery
#   time as the score
# - need to test for membership
# - need to be able to add or fail to add to the queue
# - need to be able to bump from the queue for higher-priority messages
#   - e.g. remove low-priority & cancel the job, add high-priority


class UserQueue:
    """A single user's view of their own notification queue. It provides an
    interface for:

    - number of messages in their queue
    - list of messsages (in order they'll be sent)

    And the ability to:

    - determine if their daily limit has been met
    - pop items in their queue
    - add items to their queue
    - tell us if their queue is full?

    Priorities (coming soon)
    - high
    - low

    """

    def __init__(self, message, limit=10, queue='default', send_func=send):
        self.conn = django_rq.get_connection('default')
        self.send_func = send_func
        self.limit = limit
        self.message = message
        self.user = message.user
        self.date_string = message.deliver_on.date().strftime("%Y-%m-%d")

        # Expire all new keys in ~24 hours
        exp = (message.deliver_on + timedelta(days=1)) - timezone.now()
        self.expire = int(exp.total_seconds())

    def _key(self, name):
        return "uq:{user_id}:{date_string}:{name}".format(
            user_id=self.user.id,
            date_string=self.date_string,
            name=name
        )

    def count(self):
        """Return the number of messages that are queued up for the day."""
        k = self._key("count")
        return int(self.conn.get(k) or 0)

    def full(self):
        """Is the queue full for this date? Returns True or False"""
        return self.count() >= self.limit

    def add(self, priority="high"):
        """Adds the message to the queue *if* there's room"""
        job = None
        if not self.full():
            # Enqueue the job...
            job = scheduler.enqueue_at(
                self.message.deliver_on,
                self.send_func,
                self.message.id
            )

            # Keep up with a list of job ids for the day
            # TODO: We need to keep a separate list for each priority, so we
            # can figure out whenter to drop some and add others once the
            # limit is met.
            self.conn.rpush(self._key(priority), job.id)

            # And count the total number of items queued up for the day.
            self.conn.incr(self._key("count"))

        return job

    def list(self, priority='high'):
        """Return a list of today's Jobs scheduled as a particular priority."""
        k = self._key(priority)
        num_items = self.conn.llen(k)
        job_ids = self.conn.lrange(k, 0, num_items)
        return [job for job in scheduler.get_jobs() if job.id in job_ids]

    def remove(self, message):
        pass  # TODO: remove a message (eg: when deleteing GCMMessage)
