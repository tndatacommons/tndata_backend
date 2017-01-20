"""
Code for sending SMS messages via Amazon SNS.
http://docs.aws.amazon.com/sns/latest/dg/SMSMessages.html

----

Additional Docs:

- Sending an SMS message.
  http://docs.aws.amazon.com/sns/latest/dg/sms_publish-to-phone.html

- Sending to multiple phone numbers:
  http://docs.aws.amazon.com/sns/latest/dg/sms_publish-to-topic.html

"""
import boto3
import re
import waffle

from django.conf import settings
from django.utils.text import slugify
from redis_metrics import metric


def format_numbers(phone_numbers):
    """Given a list of phone numbers, ensure they're in a valid format (E.164).

    This function will clean up any punctuation & include +1 for numbers missing
    a country code."""

    # Make sure we have them in a numbers-only format.
    numbers = [re.findall(r'\d+', n) for n in phone_numbers]
    numbers = filter(None, [''.join(n) for n in numbers])
    numbers = ["+1{}".format(n) if not n.startswith("+") else n for n in numbers]
    return numbers


def format_topic_name(topic_name):
    """Format a Topic Name for an SNS topic.

    Constraints: Topic names must be made up of only uppercase and lowercase
    ASCII letters, numbers, underscores, and hyphens, and must be between 1
    and 256 characters long.
    """
    return slugify(topic_name).lower()[:256]


def get_client(client_type='sns'):
    config = {
        'aws_access_key_id': settings.AWS_ACCESS_KEY_ID,
        'aws_secret_access_key': settings.AWS_SECRET_ACCESS_KEY,
        'region_name': 'us-east-1',
    }
    return boto3.client(client_type, **config)


def send_to(message, phone_number):
    """Send a message to a single phone number."""

    if not waffle.switch_is_active('notifications-sms'):
        return None

    # Phone numbers must use E.164 format: https://en.wikipedia.org/wiki/E.164
    # If not, assume we're in the US.
    numbers = format_numbers([phone_number])
    if len(numbers) > 0:
        phone_number = numbers[0]

    # limit to 140chars
    message = message[:140]
    if message and phone_number:
        try:
            sns_client = get_client()

            response = sns_client.publish(
                PhoneNumber=phone_number,
                Message=message
                # TopicArn='string', (Optional - can't be used with PhoneNumer)
                # TargetArn='string', (Optional - can't be used with PhoneNumer)
                # Subject='string', (Optional - not used with PhoneNumer)
                # MessageStructure='string' (Optional)
            )
            metric('SMS Message Sent', category='Notifications')
            return response
        except:
            metric('SMS Message Failed', category='Notifications')
            return None


def subscribe_to_topic(phone_numbers, topic_name, client=None):
    """Given a list/iterable of phone numbers, subscribe them to the given
    Topic so they can all be messaged simultaneously.

    - phone_numbers: list of phone numbers to subscribe. Must be in E.164 format.
    - topic_name: String - the topic name.

    Returns the TopicArn.

    """
    if client is None:
        client = get_client()

    # 1. Create the topic if it doesn't exist (this is idempotent) [CreateTopic]
    # https://boto3.readthedocs.io/en/latest/reference/services/sns.html#SNS.Client.create_topic
    topic = client.create_topic(Name=format_topic_name(topic_name))
    topic_arn = topic['TopicArn']

    # 2. Add SMS Subscribers [Subscribe]
    # https://boto3.readthedocs.io/en/latest/reference/services/sns.html#SNS.Client.subscribe
    #
    # For the sms protocol, the endpoint is a phone number of an SMS-enabled device
    for number in format_numbers(phone_numbers):
        client.subscribe(
            TopicArn=topic_arn,
            Protocol='sms',
            Endpoint=number
        )
    return topic_arn


def send_to_topic(message, topic_name=None, topic_arn=None):
    """Send the given message to an AWS SNS Topic.


    """
    if not waffle.switch_is_active('notifications-sms'):
        return None

    if all([topic_name is None, topic_arn is None]):
        raise ValueError("Either topic_name or topic_arn is required")

    # limit to 140chars
    message = message[:140]

    # Get an SNS client.
    client = get_client()

    if topic_arn is None and topic_name:
        # Get or Create the topic if it doesn't exist (this is idempotent)
        topic = client.create_topic(Name=format_topic_name(topic_name))
        topic_arn = topic['TopicArn']

    # Publish the message to the topic. [Publish]
    # https://boto3.readthedocs.io/en/latest/reference/services/sns.html#SNS.Client.publish
    return client.publish(Message=message, TopicArn=topic_arn)


def mass_send(phone_numbers, message, topic_name):
    """Send a mass  text message"""
    if phone_numbers and message and topic_name:
        arn = subscribe_to_topic(phone_numbers, topic_name)
        send_to_topic(message, topic_arn=arn)
