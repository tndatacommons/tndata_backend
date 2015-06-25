from django.conf import settings

try:
    import slack
    import slack.chat

    slack.api_token = settings.SLACK_API_TOKEN

except ImportError:
    slack = None


def post_message(channel, message):
    """Post a message in a Slack Channel.

    e.g. to post in Tech:

        post_message("#tech", "hello world")

    """
    if slack:
        return slack.chat.post_message(
            channel,
            message,
            username=settings.SLACK_USERNAME
        )
