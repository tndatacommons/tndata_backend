"""
Signal Handlers for our models.

"""
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import ObjectDoesNotExist
from django.db.models.signals import (
    pre_delete, pre_save, post_delete, post_save
)
from django.dispatch import receiver
from django.utils import timezone

from notifications.signals import notification_snoozed
from redis_metrics import metric

from .custom import CustomAction
from .packages import PackageEnrollment
from .progress import DailyProgress, UserCompletedAction
from .public import Action, Behavior, Category, Goal, action_unpublished
from .users import UserAction, UserBehavior, UserCategory, UserGoal
from .triggers import Trigger

from ..utils import clean_title, clean_notification, strip


@receiver(post_save, sender=CustomAction, dispatch_uid="coru_daily_progress")
@receiver(post_save, sender=UserBehavior, dispatch_uid="coru_daily_progress")
@receiver(post_save, sender=UserAction, dispatch_uid="coru_daily_progress")
def create_or_update_daily_progress(sender, instance, created, raw, using, **kwargs):
    """When a CustomAction, UserAction or UserBehavior is created, we want to
    create (if necessary) or update the day's DailyProgress for the user.
    """
    if created:
        dp = DailyProgress.objects.for_today(instance.user)
        dp.update_stats()
        dp.save()


@receiver(post_delete, sender=CustomAction, dispatch_uid="coru_daily_progress")
@receiver(post_delete, sender=UserBehavior, dispatch_uid="coru_daily_progress")
@receiver(post_delete, sender=UserAction, dispatch_uid="coru_daily_progress")
def update_daily_progress(sender, instance, using, **kwargs):
    """When a CustomAction, UserAction or UserBehavior is deleted, we want to
    update the day's DailyProgress again to reflect the change.
    """
    dp = DailyProgress.objects.for_today(instance.user)
    dp.update_stats()
    dp.save()


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
@receiver(pre_save, sender=Behavior)
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
@receiver(post_delete, sender=Behavior)
@receiver(post_delete, sender=Goal)
@receiver(post_delete, sender=Category)
def delete_model_icon(sender, instance, using, **kwargs):
    """Once a model instance has been deleted, this will remove its `icon` from
    the filesystem."""
    if hasattr(instance, 'icon') and instance.icon:
        instance.icon.delete()


@receiver(post_delete, sender=Action)
@receiver(post_delete, sender=Behavior)
def delete_model_image(sender, instance, using, **kwargs):
    """Once a model instance has been deleted, this will remove its `image`
    from the filesystem."""
    if hasattr(instance, 'image') and instance.image:
        instance.image.delete()


@receiver(pre_delete, sender=UserGoal, dispatch_uid="del_goal_behaviors")
def delete_goal_child_behaviors(sender, instance, using, **kwargs):
    """If a user is removing a goal, delete all of the user's selected
    behaviors that have *no other* parent goal."""
    # Get a list of all goals selected by the user, excluding the one
    # we're about to remove.
    user_goals = UserGoal.objects.filter(user=instance.user)
    user_goals = user_goals.exclude(id=instance.id)
    user_goals = user_goals.values_list('goal', flat=True)

    # Delete all the user's behaviors that lie ONLY in the goal we're
    # about to remove
    user_behaviors = instance.user.userbehavior_set.all()
    user_behaviors = user_behaviors.exclude(behavior__goals__in=user_goals)
    user_behaviors.delete()


@receiver(pre_delete, sender=UserBehavior, dispatch_uid="del_behavior_actions")
def delete_behavior_child_actions(sender, instance, using, **kwargs):
    """If a user is removing a behavior, delete all of the user's selected
    actions that are a child of this behavior."""

    user_actions = instance.user.useraction_set.filter(
        action__behavior=instance.behavior
    )
    user_actions.delete()


@receiver(post_delete, sender=UserBehavior)
def remove_behavior_reminders(sender, instance, using, **kwargs):
    """If a user deletes ALL of their UserBehavior instances, we should also
    remove the currently-queued GCMMessage for the Behavior reminder.

    """
    # NOTE: All behavior reminders use the default trigger, and we're not
    # actually connecting them to any content types, so that's null.
    if not UserBehavior.objects.filter(user=instance.user).exists():
        try:
            from notifications.models import GCMMessage
            messages = GCMMessage.objects.for_model("behavior", include_null=True)
            messages = messages.filter(user=instance.user)
            messages.delete()
        except (ImportError, ContentType.DoesNotExist):
            pass


@receiver(post_save, sender=UserAction, dispatch_uid="create-parent-userbehavior")
def create_parent_user_behavior(sender, instance, using, **kwargs):
    """If a user doens't have a UserBehavior object for the UserAction's
    parent behavior this will create one.

    """
    params = {'user': instance.user, 'behavior': instance.action.behavior}
    if not UserBehavior.objects.filter(**params).exists():
        UserBehavior.objects.create(
            user=instance.user,
            behavior=instance.action.behavior
        )


@receiver(post_save, sender=UserAction, dispatch_uid="create-relative-reminder")
def create_relative_reminder(sender, instance, created, raw, using, **kwargs):
    """When a UserAction is created, we need to look at it's default_trigger
    and see if it's a relative reminder. If so, we automatically create a
    custom trigger for the user filling in it's trigger_date based on the
    UserAction's creation date.

    """
    is_relative = (
        instance.custom_trigger is None and
        instance.default_trigger is not None and
        instance.default_trigger.is_relative
    )
    if created and is_relative:
        trigger = Trigger.objects.create(
            user=instance.user,
            name="Trigger for {}".format(instance),
            time=instance.default_trigger.time,
            trigger_date=instance.default_trigger.trigger_date,
            recurrences=instance.default_trigger.recurrences,
            start_when_selected=instance.default_trigger.start_when_selected,
            stop_on_complete=instance.default_trigger.stop_on_complete,
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
@receiver(post_save, sender=UserBehavior, dispatch_uid="adopt_userbehaviors")
@receiver(post_save, sender=UserAction, dispatch_uid="adopt_useractions")
def user_adopted_content(sender, instance, created, raw, using, **kwargs):
    """Record some metrics when a user adopts a piece of behavior content."""
    if created:
        key = "{}-created".format(sender.__name__.lower())
        metric(key, category="User Interactions")


@receiver(pre_save, sender=UserAction, dispatch_uid='bust_useraction_cache')
@receiver(pre_save, sender=UserBehavior, dispatch_uid='bust_userbehavior_cache')
@receiver(pre_save, sender=UserGoal, dispatch_uid='bust_usergoal_cache')
@receiver(pre_save, sender=UserCategory, dispatch_uid='bust_usercategory_cache')
def bust_cache(sender, instance, raw, using, **kwargs):
    """This is a little messy, but whenever a user's mapping to content is saved
    we need to bust some cache values. This is mostly for the giant api endpoint
    that exposes a lot of user data (e.g. in the userprofile app).

    # TODO: extend this to bust all cache keys related to User* objects?

    """
    # A mapping of model to cache keys
    cache_key = {
        UserAction: '{}-User.get_actions',
        UserBehavior: '{}-User.get_behaviors',
        UserGoal: '{}-User.get_goals',
        UserCategory: '{}-User.get_categories',
    }
    cache_key = cache_key.get(sender, None)
    if cache_key:
        cache_key = cache_key.format(instance.user.id)
        cache.delete(cache_key)


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
