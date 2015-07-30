from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string

from utils.email import send_mass_html_mail


def send_package_enrollment_batch(emails, categories, subject=None):
    """Send the notification email to those users who have been enrolled.

    * emails is a list of email addresses (but their accounts should be created
      at this point).
    * categories is a queryset of Category objects.
    * subject: optional; subject to use for the email.

    """
    if subject is None:
        subject = "Welcome to {0}".format(", ".join([c.title for c in categories]))

    User = get_user_model()
    users = User.objects.filter(email__in=emails)
    users = users.values_list("email", "username", "is_active")
    email_data = []
    for email, username, is_active in users:
        # datatuple for send_mass_html_mail is:
        # (subject, message, html_message, from_email, recipient_list)
        cta_link = "{0}{1}".format(
            settings.SITE_URL,
            reverse("goals:accept-enrollment", args=[username])
        )
        context = {
            "alert": "You're enrolled!",
            "email": email,
            "username": username,
            "new_user": not is_active,  # User was just created, needs to activate.
            "categories": categories,
            "cta_link": cta_link,
            "cta_text": "Get Started",
        }
        email_data.append((
            subject,
            render_to_string("goals/email/package_enrollment.txt", context),
            render_to_string("goals/email/package_enrollment.html", context),
            settings.DEFAULT_FROM_EMAIL,
            [email],
        ))

    return send_mass_html_mail(email_data, fail_silently=False)
