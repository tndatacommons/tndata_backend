import logging
import sys
import traceback

from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from redis_metrics import metric
import django_rq
import waffle

from utils.slack import post_private_message


logger = logging.getLogger("loggly_logs")


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
        msg.send()  # NOTE: sets a metric on successful sends.
    except Exception as e:
        # NOTE: If for some reason, a message got queued up, but something
        # happend to the original GCMMessage, and it's pre-delete signal handler
        # failed, we'd get this exception. OR if something happend during
        # delivery to GCM, we'd get here.
        exc_type, exc_value, exc_traceback = sys.exc_info()

        args = ("notifications.queue.send()", e, settings.SITE_URL, message_id)
        log = "FAILED: {}\n{} on {} for id = {}".format(*args)
        logger.error(log.replace("\n", ""))

        # Include the traceback in the slack message.
        tb = traceback.format_exception(exc_type, exc_value, exc_traceback)
        log = "{}\n```{}```".format(log, "\n".join(tb))
        post_private_message("bkmontgomery", log)


def enqueue(message, threshold=24, save=True):
    """Given a GCMMessage object, add it to the queue of messages to be sent.

    - message: An instance of a GCMMessage
    - threshold: Number of hours in advance that we schedule notifications.
    - save: (boolean) should we save the message after we add the job id?

    """
    job = None

    # Only queue up messages for the next 24 hours (or messages that should
    # have been sent within the past hour)
    now = timezone.now() - timedelta(hours=1)
    threshold = now + timedelta(hours=threshold)
    is_upcoming = now < message.deliver_on and message.deliver_on < threshold

    if message.user and is_upcoming:
        if waffle.switch_is_active('notifications-user-userqueue'):
            # Enqueue messages through the UserQueue.
            job = UserQueue(message).add(save=save)
        else:
            job = scheduler.enqueue_at(message.deliver_on, send, message.id)

        # Save the job ID on the GCMMessage, so if it gets re-enqueued we
        # can cancel the original?
        if save:
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


class TotalCounter:
    """Descriptor to count total number of queued messages for the UserQueue.
    This class persists its value in redis, but gives us a nicer interface
    for changing the value."""

    def __init__(self):
        self.conn = django_rq.get_connection('default')

    def __get__(self, instance, owner):
        # Use the instance's key to retrieve the value.
        count = int(self.conn.get(instance._key("count")) or 0)
        return count if count > 0 else 0  # Never drop lower than zero

    def __set__(self, instance, value):
        if value <= 0:
            value = 0
        key = instance._key("count")
        self.conn.set(key, value)
        self.conn.expire(key, timedelta(days=2))
        return value


class UserQueue:
    """This class implements a single user's view of their own queue of
    notifications (GCMMessages) for a given day. It stores details in redis,
    and knows how to schedule a message for delivery using rq-scheduler.

    ## Priorities.

    A GCMMessage has a priority, and the UserQueue (this class) will respect
    that, queueing up messages for delivery at the correct priority, while
    respeciting the overall limit (total number of messages to be sent for
    the day). For example, we currently support the following queues:

    - low: typically these messages are the least important, and will be the
      first messages bumped from delivery once the limit is met.
    - medium: ...
    - high: ... High-priority queues are reserved for the **most important**
      messages that must be delivered. This queue ignores the daily limit, so
      it's possible to go over the limit (use as a last resort).

    ## Methods

    - count: Total number of messages queued up for delivery for the day.
    - full : Boolean: are we at (or over) the daily limit
    - add: Add a message to the queue and schedule it for delivery, returning
      a Job or None (if adding failed)
    - list: Return a list of job IDs
    - remove: Remove the message from the queue.

    ## Examples: TODO

    """
    count = TotalCounter()  # Total Counter for all daily messages

    def __init__(self, message, queue='default', send_func=send):
        self.conn = django_rq.get_connection('default')
        self.send_func = send_func
        self.message = message
        self.limit = message.get_daily_message_limit()
        self.priority = getattr(message, 'priority', 'low')
        self.user = message.user
        self.date_string = message.deliver_on.date().strftime("%Y-%m-%d")

        # Since we only queue up messages 24 hours in advance, we can
        # auto-expire any values after a couple days. This can be a timedelta
        # object;
        self.expire = timedelta(days=2)

    def _key(self, name):
        """Construct a redis key for the given name. Keys are of the form:

            uq:{user_id}:{date_string}:{name}

        For example:

            uq:1:2016-02-10:count   -- Total daily message count.
            uq:1:2016-02-10:low     -- Key for the low-priority queue.
            uq:1:2016-02-10:high    -- Key for the high-priority queue.

        Returns a string.

        """
        return "uq:{user_id}:{date_string}:{name}".format(
            user_id=self.user.id,
            date_string=self.date_string,
            name=name
        )

    @staticmethod
    def clear(user, date=None):
        """Clear all of the redis queue data associated with the given user
        for the given date (or today)."""
        if date is None:
            date = timezone.now()
        date_string = date.strftime("%Y-%m-%d")
        conn = django_rq.get_connection('default')

        # Redis keys for the count, and all queues.
        keys = [
            'uq:{user_id}:{date_string}:count',
            'uq:{user_id}:{date_string}:low',
            'uq:{user_id}:{date_string}:medium',
            'uq:{user_id}:{date_string}:high',
        ]
        keys = [k.format(user_id=user.id, date_string=date_string) for k in keys]
        conn.delete(*keys)

    @staticmethod
    def get_data(user, date=None):
        """Return a dict of data (redis keys/values) for the UserQueue for the
        given date."""
        if date is None:
            date = timezone.now()
        date_string = date.strftime("%Y-%m-%d")
        conn = django_rq.get_connection('default')

        # Redis keys for the count, and all queues.
        keys = [
            'uq:{user_id}:{date_string}:count',
            'uq:{user_id}:{date_string}:low',
            'uq:{user_id}:{date_string}:medium',
            'uq:{user_id}:{date_string}:high',
        ]
        keys = [k.format(user_id=user.id, date_string=date_string) for k in keys]

        # Get the list values, and convert them from bytes to utf
        data = {k: conn.lrange(k, 0, 100) for i, k in enumerate(keys) if i > 0}
        for key, values in data.items():
            data[key] = [v.decode('utf8') for v in values]
        data[keys[0]] = int(conn.get(keys[0]))  # then include the count
        return data

    @property
    def num_low(self):
        return self.conn.llen(self._key("low"))

    @property
    def num_medium(self):
        return self.conn.llen(self._key("medium"))

    @property
    def num_high(self):
        return self.conn.llen(self._key("high"))

    def full(self):
        """Is the user's daily queue full? Returns True or False"""
        return self.count >= self.limit

    def _enqueue(self, save=True):
        """Put the message in the appropriate queue and schedule for delivery,
        taking care to update the total count. This method also adds the Job's
        ID to the message & saves it."""
        # Enqueue the job...
        job = scheduler.enqueue_at(
            self.message.deliver_on,
            self.send_func,
            self.message.id
        )
        if save:
            self.message.queue_id = job.id
            self.message.save()

        # Keep up with a list of job ids for the day.
        # We need to keep a separate list for each priority, so we
        # can figure out whenter to drop some and add others once the
        # limit is met.
        key = self._key(self.priority)
        self.conn.rpush(key, job.id)
        self.conn.expire(key, self.expire)

        # And count the total number of items queued up for the day.
        self.count += 1
        return job

    def add(self, save=True):
        """Adds the message to the queue *if* there's room. IF the message was
        added, it's `queue_id` gets set, and it gets saved (by default). This
        behavior can be turned off by passing `save=False`

        Returns the scheduled Job object (or None if the job was not added).

        """
        # Scenarios:
        #
        # Queue is not full. Schedule it.
        # Queue is full, msg is high priority. Schedule it.
        # Queue is full, msg is medium priority, try to bump a low priority msg,
        #   then schedule.
        # Queue is full, msg is low priority, ignore.

        job = None
        if not self.full() or self.priority == 'high':
            job = self._enqueue(save=save)
        elif self.priority == 'medium' and self.num_low > 0:
            # Bump a lower-priority message
            self.bump_from_queue('low')
            job = self._enqueue(save=save)
        return job

    def list(self):
        """Return a list of today's Jobs scheduled at the same priority as
        the current Message."""
        k = self._key(self.priority)
        num_items = self.conn.llen(k)

        # Get all the job ids stored at the given priority.
        job_ids = self.conn.lrange(k, 0, num_items)

        # Redis returns data in bytes, so we need to decode to utf-8
        job_ids = [job_id.decode('utf8') for job_id in job_ids]
        return [job for job in scheduler.get_jobs() if job.id in job_ids]

    def bump_from_queue(self, priority='low'):
        """Bump a message from a queue (ie. remove an already-queued message in
        favor of a higher-priority one.

        This removes the items from the end of the given priority queue, and
        cancels it's scheduled delivery.

        """
        # Remove the item from the priority queue
        job_id = self.conn.rpop(self._key(priority))
        job_id = job_id.decode('utf8')

        # Decrement the total count.
        self.count -= 1

        # And cancel the job (it's ok if this already happened)
        cancel(job_id)

    def remove(self):
        """Remove the message (eg: when deleteing GCMMessage)"""
        k = self._key(self.priority)

        # Pull all the job ids off the queue (we'll re-add them later), keeping
        # the ones we're not removing
        job_ids = [
            job_id for job_id in self.list()
            if job_id != self.message.queue_id
        ]

        # Then delete the queue, and re-add the keepers.
        self.conn.delete(k)
        if len(job_ids) > 0:
            self.conn.rpush(k, *job_ids)

        # Decrement the total count.
        self.count -= 1

        # And cancel the job (it's ok if this already happened)
        cancel(self.message.queue_id)
