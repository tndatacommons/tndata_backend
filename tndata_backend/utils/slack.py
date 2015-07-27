from django.conf import settings

try:
    import slack
    import slack.chat
    import slack.users
    slack.api_token = settings.SLACK_API_TOKEN
except ImportError:
    slack = None


def post_private_message(slack_user, message):
    """Post a private message to a slack user (their slack username).

    Apears to arrive from Slackbot.

    """
    user_id = None
    if slack:

        users = slack.users.list()
        if users['ok']:
            for u in users['members']:
                if u['name'] == slack_user:
                    user_id = u['id']

    if user_id is not None:
        post_message(user_id, message)


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


def log_message(gcm_message, event, tfmt="%Y-%m-%d %H:%I:%S%z"):
    """Log some details about a GCM Message.  This is some
    temporary code to let me track the lifespace of messages
    for a specific user."""

    if gcm_message.user.email == "brad@brad.tips":
        message = (
            "{event}\nID: {id}\nCreated: {created}\n"
            "Deliver On: {deliver}\nTitle: {title}\n"
        )
        message = message.format(
            event=event,
            id=gcm_message.message_id,
            created=gcm_message.created_on.strftime(tfmt),
            deliver=gcm_message.deliver_on.strftime(tfmt),
            title=gcm_message.title
        )
        post_message("#tech", message)
