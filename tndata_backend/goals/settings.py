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
