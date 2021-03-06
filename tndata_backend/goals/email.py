from django.conf import settings
from django.template.loader import render_to_string

from utils.email import send_mass_html_mail


def send_package_cta_email(request, enrollments, cta_link=None, cta_text=None,
                           message=None, subject=None):
    """Send an arbitrary email to users enrolled in a package.

    * request: an HttpRequest instance.
    * enrollments: A QuerySet of the newly created PackageEnrollment objects.
    * message: A message to display to the users.
    * subject: The email subject.
    * cta_link: A link for users to click
    * cta_text: The text of the link's button.

    """
    cta_text = "Click Here" if cta_text is None else cta_text

    email_data = []
    for pe in enrollments:
        # datatuple for send_mass_html_mail is:
        # (subject, message, html_message, from_email, recipient_list)

        if subject is None:
            subject = "New Message from {0}".format(pe.category)

        context = {
            "message": message,
            "email": pe.user.email,
            "alert": pe.category,
            "cta_link": cta_link,
            "cta_text": cta_text,
        }
        email_data.append((
            subject,
            render_to_string("goals/email/package_cta_email.txt", context),
            render_to_string("goals/email/package_cta_email.html", context),
            settings.DEFAULT_FROM_EMAIL,
            [pe.user.email],
        ))

    return send_mass_html_mail(email_data, fail_silently=False)


def send_package_enrollment_batch(request, enrollments, message=None):
    """Send the notification email to those users who have been enrolled.

    * request: an HttpRequest instance.
    * enrollments: A QuerySet of the newly created PackageEnrollment objects.
    * message: An optional message to display to the users. If provided, this
      will replace the default body content of the email.

    """
    cta_link = None
    cta_text = None

    email_data = []
    for pe in enrollments:
        # datatuple for send_mass_html_mail is:
        # (subject, message, html_message, from_email, recipient_list)

        subject = "Welcome to {0}".format(pe.category)

        if not pe.accepted:
            cta_link = request.build_absolute_uri(pe.get_accept_url())
            cta_text = "Get Started"

        context = {
            "message": message,
            "alert": "You're enrolled!",
            "email": pe.user.email,
            "username": pe.user.username,
            "accepted": pe.accepted,  # They need to accept the consent.
            "new_user": not pe.user.is_active,  # They need the app.
            "category": pe.category,
            "goals": pe.goals.all(),
            "cta_link": cta_link,
            "cta_text": cta_text,
        }
        email_data.append((
            subject,
            render_to_string("goals/email/package_enrollment.txt", context),
            render_to_string("goals/email/package_enrollment.html", context),
            settings.DEFAULT_FROM_EMAIL,
            [pe.user.email],
        ))

    return send_mass_html_mail(email_data, fail_silently=False)
