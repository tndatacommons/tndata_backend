"""
A utilty module to make it easier to delete a user's related application data.

"""
from django_rq import job


USER_OBJECT_TYPES = [
    ('awards', 'Badges', "Delete all of the user's awarded Badges"),
    ('customgoal', 'Custom Goals', "Delete all of the user's custom goals"),
    ('customaction', 'Custom Actions', "Delete all of the user's custom actions"),
    ('usercompletedcustomaction', 'Completed Custom Actions',
        "Delete all of the user's history of completed custom actions"),
    ('customactionfeedback', 'Custom Action Feedback',
        "Delete all of the user-supplied feedback associated with their "
        "custom actions"),
    ('useraction', 'Actions', "Remove the user's selected Action data"),
    ('usergoal', 'Goals', "Remove the user's selected Goal data"),
    ('usercategory', 'Categories',
        "Remove the user's selected Categories. This will also force them"
        " through onboarding again"),
    ('trigger', 'Triggers', "Remove the user's custom triggers"),
    ('usercompletedaction', 'Completed Actions',
        "Remove the user's history of completed actions"),
    ('dailyprogress', 'Daily Progress',
        "Remove the user's daily progress snapshots"),
    ('packageenrollment', 'Package Enrollment', "Remove the user from all packages"),
    ('program', 'Program Membership', "Remove the user from all programs"),
    ('organization', 'Organization Membership',
        "Remove the user from all organizations"),
    ('gcmdevice', 'GCM Devices', "Delete all registered devices"),
    ('gcmmessage', 'GCM Messages', "Delete all queued GCM Messages"),
]


@job
def _do_object_removal(users, items_to_remove):
    for user in users:
        for item in items_to_remove:
            if item == "awards":
                user.badges.all().delete()  # removes the user's Awards
            elif item == "program":
                for program in user.program_set.all():
                    program.members.remove(user)
            elif item == "organization":
                for org in user.member_organizations.all():
                    org.members.remove(user)
                for org in user.admin_organizations.all():
                    org.admins.remove(user)
                for org in user.staff_organizations.all():
                    org.staff.remove(user)
            else:
                # e.g. call: user.useraction_set.all().delete()
                attr = "{}_set".format(item)
                getattr(user, attr).all().delete()

    # If we removed categories, we ned to reset the user's onboarding status.
    if 'usercategory' in items_to_remove:
        user.userprofile.needs_onboarding = True
        user.userprofile.save()


def remove_app_data(users, items_to_remove, async=True):
    """Remove application data for a set of users.

    - users: a queryset of users for whom we want to delete data.
    - items_to_remove: a list of strings corresponding to items from the
      USER_OBJECT_TYPES list.
    - async: if True (the default) this will run asynchronously.

    """
    if async:
        return _do_object_removal.delay(users, items_to_remove)
    else:
        return _do_object_removal(users, items_to_remove)
