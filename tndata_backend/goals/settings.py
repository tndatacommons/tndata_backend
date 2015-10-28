"""
Custom settings for the Goals app.

"""
from django.conf import settings as default_settings


# We should always have a default Trigger for all Behaviors.
# By convention, it's name is 'Default Behavior Reminder', but this can
# be configured with the following setting.
DEFAULT_BEHAVIOR_TRIGGER_NAME = getattr(
    default_settings,
    'DEFAULT_BEHAVIOR_TRIGGER_NAME',
    'Default Behavior Reminder'
)

# The default trigger time, in 24-hour format; e.g. HH:MM
DEFAULT_BEHAVIOR_TRIGGER_TIME = getattr(
    default_settings,
    'DEFAULT_BEHAVIOR_TRIGGER_TIME',
    '07:30'
)

# The default trigger recurrence rule as a RFC2445 unicode string.
# The default value is Every day.
DEFAULT_BEHAVIOR_TRIGGER_RRULE = getattr(
    default_settings,
    'DEFAULT_BEHAVIOR_TRIGGER_RRULE',
    'RRULE:FREQ=DAILY'
)

# -----------------------------------------------------------------------------
# Similarly, we have default values for the Morning/Evening Goal reminder(s).
# -----------------------------------------------------------------------------
DEFAULT_MORNING_GOAL_TRIGGER_NAME = getattr(
    default_settings,
    'DEFAULT_MORNING_GOAL_TRIGGER_NAME',
    'Default Morning Goal Trigger'
)
DEFAULT_MORNING_GOAL_TRIGGER_TIME = getattr(
    default_settings,
    'DEFAULT_MORNING_GOAL_TRIGGER_TIME',
    '07:30'
)
DEFAULT_MORNING_GOAL_TRIGGER_RRULE = getattr(
    default_settings,
    'DEFAULT_MORNING_GOAL_TRIGGER_RRULE',
    'RRULE:FREQ=DAILY'
)
DEFAULT_MORNING_GOAL_NOTIFICATION_TITLE = getattr(
    default_settings,
    'DEFAULT_MORNING_GOAL_TRIGGER_RRULE',
    'Review your day'
)
DEFAULT_MORNING_GOAL_NOTIFICATION_TEXT = getattr(
    default_settings,
    'DEFAULT_MORNING_GOAL_TRIGGER_RRULE',
    'Check in with Compass to stay on track'
)

DEFAULT_EVENING_GOAL_TRIGGER_NAME = getattr(
    default_settings,
    'DEFAULT_EVENING_GOAL_TRIGGER_NAME',
    'Default Evening Goal Trigger'
)
DEFAULT_EVENING_GOAL_TRIGGER_TIME = getattr(
    default_settings,
    'DEFAULT_EVENING_GOAL_TRIGGER_TIME',
    '16:30'
)
DEFAULT_EVENING_GOAL_TRIGGER_RRULE = getattr(
    default_settings,
    'DEFAULT_EVENING_GOAL_TRIGGER_RRULE',
    'RRULE:FREQ=DAILY'
)
DEFAULT_EVENING_GOAL_NOTIFICATION_TITLE = getattr(
    default_settings,
    'DEFAULT_EVENING_GOAL_TRIGGER_RRULE',
    'How are you doing?'
)
DEFAULT_EVENING_GOAL_NOTIFICATION_TEXT = getattr(
    default_settings,
    'DEFAULT_EVENING_GOAL_TRIGGER_RRULE',
    'Check in to track your progress'
)
