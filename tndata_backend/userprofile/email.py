from django.conf import settings
from django.core.validators import validate_email
from django.template.loader import render_to_string

from utils.email import send_mass_html_mail


def _is_valid(email):
    try:
        validate_email(email)
        return True
    except:
        return False


def send_account_disabled_notification(emails):
    """Send an email notification to users whose account has been disabled.

    * emails: a list of email addresses

    """
    subject = "Your account has been disabled"
    cta_link = None
    cta_text = None
    email_data = []
    emails = [email for email in emails if _is_valid(email)]

    for email in emails:
        # datatuple for send_mass_html_mail is:
        # (subject, message, html_message, from_email, recipient_list)
        context = {"alert": subject, "cta_link": cta_link, "cta_text": cta_text}
        email_data.append((
            subject,
            render_to_string("userprofile/email/disabled.txt", context),
            render_to_string("userprofile/email/disabled.html", context),
            settings.DEFAULT_FROM_EMAIL,
            [email],
        ))

    return send_mass_html_mail(email_data, fail_silently=False)
