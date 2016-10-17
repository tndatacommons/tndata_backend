"""
Custom settings for the Goals app.

"""
from django.conf import settings as default_settings


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
    '20:00'
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
