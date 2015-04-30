"""
This module provides permissions and Group-based tools. This app defines two
custom groups for people who create and review content:

1. Content Authors: Have Read, create, update permissions for content models;
   (Goals, Behaviors, Actions) and read for Categories.
2. Content Editors: Have the above plus the ability to delete and publish or
   decline content created by authors.

"""
# NOTE: Dont' import any models directly; the functions here are called from
# a migration, so let's import from an AppConfig if at all possible.
from django.contrib.auth.decorators import user_passes_test
from utils.permissions import _get_group_and_permission

# Group Names
CONTENT_AUTHORS = "Content Authors"
CONTENT_EDITORS = "Content Editors"


def get_or_create_content_authors(apps=None, schema_editor=None):
    """Creates the 'Content Authors' Group, and adds the appropriate
    permissions.

    This accepts `apps` and `schema_editor` arguments so it can be called
    from a Migration.

    NOTE that this functions attempts to be idempotent, so new permissions
    will not be created if the Group already exists.
    """
    Group, Permission = _get_group_and_permission(apps)
    group, created = Group.objects.get_or_create(
        name=CONTENT_AUTHORS
    )
    if created:
        perms = [
            "view_category",
            "view_trigger",
        ]
        for obj in ['goal', 'behavior', 'action']:
            perms.append("add_{0}".format(obj))
            perms.append("change_{0}".format(obj))
            perms.append("view_{0}".format(obj))
        group.permissions = Permission.objects.filter(codename__in=perms)
    return group


def get_or_create_content_editors(apps=None, schema_editor=None):
    """Creates the 'Content Editors' Group, and adds the appropriate
    permissions.

    This accepts `apps` and `schema_editor` arguments so it can be called
    from a Migration.

    NOTE that this functions attempts to be idempotent, so new permissions
    will not be created if the Group already exists.
    """
    Group, Permission = _get_group_and_permission(apps)
    group, created = Group.objects.get_or_create(
        name=CONTENT_EDITORS
    )
    if created:
        perms = []
        for obj in ['category', 'goal', 'behavior', 'action', 'trigger']:
            perms.append("add_{0}".format(obj))
            perms.append("change_{0}".format(obj))
            perms.append("view_{0}".format(obj))
            perms.append("delete_{0}".format(obj))
            perms.append("publish_{0}".format(obj))
            perms.append("decline_{0}".format(obj))
        group.permissions = Permission.objects.filter(codename__in=perms)
    return group


# Permission Check Functions
# --------------------------

def superuser_required(user):
    """Verifies that a user is authenticated and a super user."""
    return user.is_authenticated() and user.is_superuser


def _is_superuser_or_in_group(user, group_name):
    """Checks for the following conditions:

    1. User is authenticated.
    2. User is a superuser, OR
    3. User is in the specified group.

    """
    return user.is_authenticated() and (
        user.is_superuser or user.groups.filter(name=group_name).exists()
    )


def can_view(view, login_url):
    """This function applies a decorator to a view to determine if a user
    should be able to view some content. Here's the criteria:

    1. If the view has a model attribute (then it's a generic model view),
       see if the user has a "view_[model]" permission.
    2. If the view is not associated with a model, just ensure they
       are authenticated.

    """
    if hasattr(view, 'model'):
        perm = "goals.{0}".format(view.model.__name__.lower())
        check = lambda u: u.is_authenticated() and u.has_perm(perm)
    elif hasattr(view, 'queryset'):
        perm = "goals.{0}".format(view.queryset.model.__name__.lower())
        check = lambda u: u.is_authenticated() and u.has_perm(perm)
    else:
        check = lambda u: u.is_authenticated()
    dec = user_passes_test(check, login_url=login_url)
    return dec(view)


def is_content_author(user):
    """Verifies that a user is authenticated and a content author (or an editor
    since editors get all author permissions as well)."""
    author = _is_superuser_or_in_group(user, CONTENT_AUTHORS)
    editor = _is_superuser_or_in_group(user, CONTENT_EDITORS)
    return (author or editor)


def is_content_editor(user):
    """Verifies that a user is authenticated and a content editor."""
    return _is_superuser_or_in_group(user, CONTENT_EDITORS)
