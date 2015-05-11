"""
This module provides permissions and Group-based tools. This app defines
custom groups for people who create and review content:


1. Content Viewers: Have read-only permissions for content models: Category,
   Goals, Behaviors, Actions.
2. Content Authors: Have Read, create, update permissions for content models;
   (Goals, Behaviors, Actions) and read for Categories.
3. Content Editors: Have the above plus the ability to delete and publish or
   decline content created by authors.

"""
from django.contrib.auth.models import Group, Permission

# Group Names
CONTENT_ADMINS = "Content Admins"
CONTENT_AUTHORS = "Content Authors"
CONTENT_EDITORS = "Content Editors"
CONTENT_VIEWERS = "Content Viewers"


class ContentPermissions:
    """This class encapsulates a list of permissions for different types
    of users. The types correspond to:

    * editors
    * authors
    * viewers

    NOTE: object-level permissions for authors are implemented in the
    ContentAuthorMixin.

    """
    # Objects in the goals app that that have CRUD perms
    _objects = ['action', 'behavior', 'category', 'goal', 'trigger']

    # Objects that authors have Create/Update permissions
    _author_objects = ['action', 'behavior', 'goal']

    # Objects with publish/decline permissions
    _workflow_objects = ['action', 'behavior', 'goal', 'trigger']

    @property
    def admins(self):
        """permissions for admins"""
        perms = []
        for obj in self._objects:
            perms.append('goals.add_{0}'.format(obj))
            perms.append('goals.change_{0}'.format(obj))
            perms.append('goals.delete_{0}'.format(obj))
            perms.append('goals.view_{0}'.format(obj))
            perms.append('goals.publish_{0}'.format(obj))
            perms.append('goals.decline_{0}'.format(obj))
        return perms

    @property
    def authors(self):
        """permissions for authors"""
        perms = self.viewers
        for obj in self._author_objects:
            perms.append('goals.add_{0}'.format(obj))
            perms.append('goals.change_{0}'.format(obj))
        return perms

    @property
    def editors(self):
        """permissions for editors"""
        perms = self.viewers + self.authors
        for obj in self._workflow_objects:
            perms.append('goals.publish_{0}'.format(obj))
            perms.append('goals.decline_{0}'.format(obj))
            perms.append('goals.delete_{0}'.format(obj))
        return perms

    @property
    def viewers(self):
        """permissions for editors"""
        return ['goals.view_{0}'.format(obj) for obj in self._objects]

ContentPermissions = ContentPermissions()  # make it act like a monad.


def _add_perms_to_group(group, perms_list):
    for perm in perms_list:
        app, code = perm.split(".")
        p = Permission.objects.get(content_type__app_label=app, codename=code)
        group.permissions.add(p)
    group.save()


def get_or_create_content_admins():
    """Creates the 'Content Admins' Group if it doesn't exist, and assigns
    the appropriate permissions to that group.

    """
    group, created = Group.objects.get_or_create(name=CONTENT_ADMINS)
    _add_perms_to_group(group, ContentPermissions.admins)
    return group


def get_or_create_content_authors():
    """Creates the 'Content Authors' Group if it doesn't exist, and assigns
    the appropriate permissions to that group.

    """
    group, created = Group.objects.get_or_create(name=CONTENT_AUTHORS)
    _add_perms_to_group(group, ContentPermissions.authors)
    return group


def get_or_create_content_editors():
    """Creates the 'Content Editors' Group if it doesn't exist, and assigns the
    appropriate permissions.

    """
    group, created = Group.objects.get_or_create(name=CONTENT_EDITORS)
    _add_perms_to_group(group, ContentPermissions.editors)
    return group


def get_or_create_content_viewers():
    """Creates the 'Content Viewers' Group if it doesn't exist, and assigns the
    appropriate permissions.

    """
    group, created = Group.objects.get_or_create(name=CONTENT_VIEWERS)
    _add_perms_to_group(group, ContentPermissions.viewers)
    return group


# --------------------------
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


def is_content_author(user):
    """Verifies that a user is authenticated and a content author (or an editor
    since editors get all author permissions as well)."""
    author = _is_superuser_or_in_group(user, CONTENT_AUTHORS)
    editor = _is_superuser_or_in_group(user, CONTENT_EDITORS)
    return (author or editor)


def is_content_editor(user):
    """Verifies that a user is authenticated and a content editor."""
    return _is_superuser_or_in_group(user, CONTENT_EDITORS)
