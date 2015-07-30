from django.core.mail import get_connection
from django.core.mail.message import EmailMultiAlternatives


def send_mass_html_mail(datatuple, fail_silently=False, auth_user=None,
                        auth_password=None, connection=None):
    """
    Given a datatuple of (subject, message, html_message, from_email,
    recipient_list), sends each message to each recipient list. Returns the
    number of emails sent.

    If from_email is None, the DEFAULT_FROM_EMAIL setting is used.
    If auth_user and auth_password are set, they're used to log in.
    If auth_user is None, the EMAIL_HOST_USER setting is used.
    If auth_password is None, the EMAIL_HOST_PASSWORD setting is used.

    NOTE: This is a variant of send_mass_mail that allows including an html
        template.

    https://docs.djangoproject.com/en/1.8/_modules/django/core/mail/#send_mass_mail

    """
    connection = connection or get_connection(
        username=auth_user,
        password=auth_password,
        fail_silently=fail_silently
    )

    messages = []
    for subject, message, html_message, sender, recipient in datatuple:

        message = EmailMultiAlternatives(
            subject, message, sender, recipient, connection=connection
        )
        if html_message:
            message.attach_alternative(html_message, "text/html")
        messages.append(message)

    return connection.send_messages(messages)
