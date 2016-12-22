"""
This is our ASGI config file.

For details, see:
https://channels.readthedocs.io/en/stable/deploying.html#run-interface-servers

"""

import os
from channels.asgi import get_channel_layer


# Check to see if we have an environment variable defining the settings,
# and if not, set a default.
if os.environ.get("DJANGO_SETTINGS_MODULE") is None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
channel_layer = get_channel_layer()
