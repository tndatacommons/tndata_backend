"""
Signal Handlers for our models.

"""
from datetime import timedelta
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import ObjectDoesNotExist
from django.db.models.signals import (
    m2m_changed, pre_delete, pre_save, post_delete, post_save
)

import django.dispatch
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify

from django_rq import job
from notifications.signals import notification_snoozed
from redis_metrics import metric
from utils.slack import post_private_message
from utils.user_utils import local_day_range

from .custom import CustomAction
from .packages import PackageEnrollment, Program
from .progress import DailyProgress, UserCompletedAction
from .public import Action, Category, Goal, action_unpublished
from .public import _enroll_program_members
from .users import UserAction, UserCategory, UserGoal
from .triggers import Trigger

from ..utils import clean_title, clean_notification, strip


# Custom signal that we can fire when we need to invalidate the cached User feed.
invalidate_feed = django.dispatch.Signal(providing_args=['user'])


@receiver(invalidate_feed)
def bust_feed_cache(sender, user, **kwargs):
    """Kind of a hack, but in certain situations, we want to kill the feed's
    cache and then re-create it. We do this by deleting it then re-setting it."""
    from goals.user_feed import feed_data, FEED_DATA_KEY

    # Delete the Cache
    cache_key = FEED_DATA_KEY.format(userid=user.id)
    cache.delete(cache_key)

    # And Re-create it.
    # TODO: Do this asychronously so the caller doesn't have to wait?
    feed_data(user)


@job
def _enroll_user_in_default_categories(user):
    for category in Category.objects.selected_by_default(state='published'):
        category.enroll(user)


@receiver(post_save, sender=settings.AUTH_USER_MODEL, dispatch_uid='auto-enroll')
def auto_enroll(sender, **kwargs):
    """Auto-enroll new users in default categories.

    This `post_save` handler for new user accounts looks up `Category` objects
    whose `selected_by_default` flag is True, and enrolls the new user in all
    content contained within that Category.

    You can skip this process for arbitary users by setting the following
    cache key, where EMAIL_SLUG is the sluggified email address for the User:

        omit-default-selections-EMAIL_SLUG


    E.g. the following will skip this process for the specified user:

        cache.set("omit-default-selections-{}".format(slugify(email)), True, 30)

    """

    created = kwargs.get('created', False)
    user = kwargs['instance']

    key = "omit-default-selections-{}".format(slugify(user.email))
    skip = bool(cache.get(key))

    if created and user and not skip:
        _enroll_user_in_default_categories.delay(kwargs['instance'])


@receiver(post_save, sender=CustomAction, dispatch_uid="coru_daily_progress")
@receiver(post_save, sender=UserAction, dispatch_uid="coru_daily_progress")
@receiver(post_save, sender=UserCompletedAction, dispatch_uid="coru_daily_progress")
def create_or_update_daily_progress(sender, instance, created, raw, using, **kwargs):
    """When a CustomAction, UserAction, or UserCompletedAction
    is created, we want to create (if necessary) or update the day's
    DailyProgress for the user.
    """
    if created:
        dp = DailyProgress.objects.for_today(instance.user)
        dp.update_stats()
        dp.save()


@receiver(post_delete, sender=CustomAction, dispatch_uid="coru_daily_progress")
@receiver(post_delete, sender=UserAction, dispatch_uid="coru_daily_progress")
def update_daily_progress(sender, instance, using, **kwargs):
    """When a CustomAction, UserAction is deleted, we want to update the day's
    DailyProgress again to reflect the change.
    """
    dp = DailyProgress.objects.for_today(instance.user)
    dp.update_stats()
    dp.save()


@receiver(m2m_changed, sender=Program.auto_enrolled_goals.through,
          dispatch_uid="program_goals_changed")
def program_goals_changed(sender, instance, **kwargs):
    """Handle the changes to Program.auto_enrolled_goals (M2M field).

    Sender: is the through model between Programs & Goals `Program_auto_enrolled_goals`
    Instance: A Program object.

    Additional kwargs:

    - model: could be Goal or Program
    - action: look for `post_add` (after we've finished adding the goal)
    - pk_set: the set of Goal PKs added

    """
    model = kwargs.get('model', None)
    action = kwargs.get('action', None)
    pk_set = kwargs.get('pk_set', set())  # Set of PKs added or removed

    if model in [Program, Goal] and action == "post_add" and len(pk_set) > 0:
        goals = instance.auto_enrolled_goals.filter(id__in=pk_set, state='published')
        for goal in goals:
            _enroll_program_members.delay(goal)


@receiver(pre_save, sender=DailyProgress, dispatch_uid='set_dp_checkin_streak')
def set_dp_checkin_streak(sender, instance, raw, using, **kwargs):
    """Query for yesterday's checkin streak value and add 1 whenever a
    DailyProgress object is saved."""
    if instance.created_on:
        yesterday = instance.created_on - timedelta(days=1)
    else:
        yesterday = timezone.now() - timedelta(days=1)
    yesterday = local_day_range(instance.user, yesterday)

    # See what "yesterday's streak value was"
    try:
        streak = DailyProgress.objects.exclude(pk=instance.id).get(
            user=instance.user,
            created_on__range=yesterday
        ).checkin_streak
    except DailyProgress.DoesNotExist:
        streak = 0
    instance.checkin_streak = streak + 1


@receiver(post_save, sender=Trigger, dispatch_uid="custom-trigger-updated")
def custom_trigger_updated(sender, instance, created, raw, using, **kwargs):
    """Record metrics when a User updates their custom triggers."""
    if instance.user:
        metric('custom-trigger-updated', category="User Interactions")


@receiver(pre_delete, sender=Trigger, dispatch_uid="trigger-remove-queued-messages")
@receiver(post_save, sender=Trigger, dispatch_uid="trigger-remove-queued-messages")
def remove_queued_messages(sender, instance, *args, **kwargs):
    """If a trigger is updated, we need to remove all currently queued GCM
    Messages that are using the trigger."""
    try:
        instance.action_default.remove_queued_messages()
    except ObjectDoesNotExist:
        pass


@receiver(pre_save, sender=Action)
@receiver(pre_save, sender=Goal)
@receiver(pre_save, sender=Category)
def clean_content(sender, instance, raw, using, **kwargs):
    # A mapping of model field names and the function that cleans them.
    clean_functions = {
        "title": clean_title,
        "subtitle": clean_title,
        "description": strip,
        "more_info": strip,
        "notification_text": clean_notification,
    }
    for field, func in clean_functions.items():
        if hasattr(instance, field):
            setattr(instance, field, func(getattr(instance, field)))


@receiver(post_delete, sender=Action)
@receiver(post_delete, sender=Goal)
@receiver(post_delete, sender=Category)
def delete_model_images(sender, instance, using, **kwargs):
    """Once a model instance has been deleted, this will remove its `icon`
    and `image` (if it has one) from the filesystem."""
    if not (settings.DEBUG or settings.STAGING or settings.TESTING):
        try:
            msg = "In `delete_model_images` for *{}* / {}\nLast updated {} by {}".format(
                sender.__name__,
                instance,
                instance.updated_on.strftime("%c %z") if instance and instance.updated_on else "n/a",
                instance.updated_by.get_full_name() if instance and instance.updated_by else "n/a"
            )

            if hasattr(instance, 'icon') and instance.icon:
                # instance.icon.delete()
                msg += "\nIcon: {}".format(instance.icon.url)

            if hasattr(instance, 'image') and instance.image:
                # instance.image.delete()
                msg += "\nImage: {}".format(instance.image.url)

            post_private_message("bkmontgomery", msg)
        except:
            pass


@receiver(post_save, sender=UserAction, dispatch_uid="create-relative-reminder")
def create_relative_reminder(sender, instance, created, raw, using, **kwargs):
    """When a UserAction is saved, we need to look at it's default_trigger
    and see if it's a relative reminder. If so, we automatically create a
    custom trigger for the user filling in it's trigger_date based on the
    UserAction's creation date.

    """
    is_relative = (
        instance.custom_trigger is None and
        instance.default_trigger is not None and
        instance.default_trigger.is_relative
    )
    # We should always check for a custom trigger in this case.
    if is_relative and not instance.custom_trigger:
        trigger = Trigger.objects.create(
            user=instance.user,
            name="Trigger for {}".format(instance),
            time_of_day=instance.default_trigger.time_of_day,
            frequency=instance.default_trigger.frequency,
            time=instance.default_trigger.time,
            trigger_date=instance.default_trigger.trigger_date,
            recurrences=instance.default_trigger.recurrences,
            start_when_selected=instance.default_trigger.start_when_selected,
            stop_on_complete=instance.default_trigger.stop_on_complete,
            disabled=instance.default_trigger.disabled,
            relative_value=instance.default_trigger.relative_value,
            relative_units=instance.default_trigger.relative_units
        )
        trigger.trigger_date = trigger.relative_trigger_date(instance.created_on)
        trigger.save()
        instance.custom_trigger = trigger
        instance.save()


@receiver(notification_snoozed)
def reset_next_trigger_date_when_snoozed(sender, message, user,
                                         related_object, deliver_on, **kwargs):
    """If a user snoozes a notification (in the notifications app), this function
    will try to update the relevant UserAction's `next_trigger_date`.

    """
    if related_object and message.content_type.name.lower() == 'action':
        ua = related_object.useraction_set.filter(user=user).first()
        if ua and deliver_on:
            ua.next_trigger_date = deliver_on
            ua.save(update_triggers=False)


@receiver(post_delete, sender=UserAction)
@receiver(action_unpublished, sender=UserAction)
def remove_action_reminders(sender, instance, using, **kwargs):
    """If a user deletes one of their UserAction instances, or if an Action
    is unpublished, we need to delete the GCMMessage associated with it.

    NOTE: GCMMessages have a generic relationship to the Action
    """
    # Remove any custom triggers associated with this object.
    try:
        if instance.custom_trigger:
            instance.custom_trigger.delete()
    except Trigger.DoesNotExist:
        # This really shouldn't happen, but sometimes it does when cleaning
        # up generated objects in our test suite
        pass

    try:
        # Remove any pending notifications
        from notifications.models import GCMMessage
        action_type = ContentType.objects.get_for_model(Action)
        messages = GCMMessage.objects.filter(
            content_type=action_type,
            object_id=instance.action.id,
            user=instance.user
        )
        messages.delete()
    except (ImportError, ContentType.DoesNotExist):
        pass


@receiver(post_save, sender=UserCompletedAction, dispatch_uid="action-completed")
def action_completed(sender, instance, created, raw, using, **kwargs):
    """Record metrics when a UserCompletedAction status is updated."""
    if instance.state:
        key = "action-{}".format(instance.state)
        metric(key, category="User Interactions")

    # Kill all of the queued messages that match this action when the trigger's
    # stop_on_complete is True
    completed = instance.state == UserCompletedAction.COMPLETED

    # Try to get the trigger (custom or default)
    trigger = instance.useraction.trigger

    if completed and trigger and trigger.stop_on_complete:
        messages = instance.user.gcmmessage_set.filter(
            object_id=instance.action.id,
            content_type=ContentType.objects.get_for_model(Action)
        )
        messages.delete()

    # Check the UserAction's primary goal. If all of the UserActions
    # within taht primary goal are completed, mark the UserGoal as completed.
    ug = instance.usergoal
    if ug and completed and instance.sibling_actions_completed():
        ug.complete()
        ug.save()


@receiver(pre_delete, sender=UserCategory, dispatch_uid="del_cat_goals")
def delete_category_child_goals(sender, instance, using, **kwargs):
    """If a user is removing a category, delete all of the user's selected
    goals that have *no other* parent category."""
    # Get a list of all categories selected by the user, excluding the one
    # we're about to remove.
    user_categories = UserCategory.objects.filter(user=instance.user)
    user_categories = user_categories.exclude(id=instance.id)
    user_categories = user_categories.values_list('category', flat=True)

    # Delete all the user's goals that lie ONLY in the category we're
    # about to remove
    user_goals = instance.user.usergoal_set.all()
    user_goals = user_goals.exclude(goal__categories__in=user_categories)
    user_goals.delete()


@receiver(post_save, sender=UserCategory, dispatch_uid="adopt_usercategories")
@receiver(post_save, sender=UserGoal, dispatch_uid="adopt_usergoals")
@receiver(post_save, sender=UserAction, dispatch_uid="adopt_useractions")
def user_adopted_content(sender, instance, created, raw, using, **kwargs):
    """Record some metrics when a user adopts a piece of content."""
    if created:
        key = "{}-created".format(sender.__name__.lower())
        metric(key, category="User Interactions")


@receiver(post_save, sender=PackageEnrollment, dispatch_uid="notifiy_for_new_package")
def notify_for_new_package(sender, instance, created, **kwargs):
    """Create and schedule a GCMMEssage for users that have a device registered,
    once they've been enrolled in a new package.

    """
    if created and instance.user.gcmdevice_set.exists():
        from notifications.models import GCMMessage
        GCMMessage.objects.create(
            user=instance.user,
            title="You've been enrolled.",
            message="Welcome to {0}".format(instance.category.title),
            deliver_on=timezone.now(),
            obj=instance,
            priority=GCMMessage.HIGH
        )
