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
from django.conf import settings
import boto3


def send_to(message="Hello World", phone_number="+18705144746"):
    """Send a message to a single phone number."""

    # Phone numbers must use E.164 format: https://en.wikipedia.org/wiki/E.164
    # If not, assume we're in the US.
    if phone_number and not phone_number.startswith("+"):
        phone_number = "+1{}".format(phone_number)

    # limit to 140chars
    message = message[:140]
    if message and phone_number:
        # See the SNS.Client.publish docs, here:
        # http://boto3.readthedocs.io/en/latest/reference/services/sns.html#SNS.Client.publish
        config = {
            'aws_access_key_id': settings.AWS_ACCESS_KEY_ID,
            'aws_secret_access_key': settings.AWS_SECRET_ACCESS_KEY,
            'region_name': 'us-east-1',
        }
        sns_client = boto3.client('sns', **config)

        response = sns_client.publish(
            PhoneNumber=phone_number,
            Message=message
            #TopicArn='string', (Optional - can't be used with PhoneNumer)
            #TargetArn='string', (Optional - can't be used with PhoneNumer)
            #Subject='string', (Optional - not used with PhoneNumer)
            #MessageStructure='string' (Optional)
        )
        #print(response)
        return response

