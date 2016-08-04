from django import template
from goals.models import Category, Goal, Action, Behavior
from utils.templatetags.util_tags import object_controls

from ..permissions import is_package_contributor

register = template.Library()


@register.inclusion_tag("goals/_action_creation_menu_items.html")
def action_creation_menu():
    return {'action_model': Action}


@register.inclusion_tag("goals/_object_controls.html", takes_context=True)
def goal_object_controls(context, obj):
    """Compile custom permissions for Goal objects, and render the util's
    _object_controls template."""

    result = object_controls(context, obj, "goals")
    user = context.request.user

    # Kind of a hack. only editors have publish_* permissions.
    editor_perm = "goals.publish_{0}".format(obj.__class__.__name__.lower())
    is_editor = user.has_perm(editor_perm)

    # Determine if the user should have certain object permissions, such as:
    # - can_update
    # - can_delete
    # - can_duplicate
    # - can_transfer
    if is_editor:
        result['can_update'] = True
        result['can_delete'] = True
        result['can_duplicate'] = True
    elif is_package_contributor(user, obj):
        result['can_update'] = True
        result['can_delete'] = False
        result['can_duplicate'] = True
    elif hasattr(obj, "is_pending"):
        # Don't allow editing pending items unless you're a publisher.
        if not is_editor and obj.is_pending:
            result['can_update'] = False
            result['can_delete'] = False
        elif not is_editor and obj.is_published:
            # Only allow users to edit their own items if published.
            result['can_update'] = (obj.created_by == user)
            result['can_delete'] = False
        elif not is_editor and result.get('can_update', False):
            # otherwise, they can do whatever to their own content.
            result['can_update'] = (obj.created_by == user)
            result['can_delete'] = (obj.created_by == user)

        # Only allow duplicating published items.
        if obj.is_pending or obj.is_draft or obj.is_declined:
            result['can_duplicate'] = False
        else:
            result['can_duplicate'] = True

    # Transfers only apply to Content instances.
    if obj.__class__ in [Category, Goal, Action, Behavior]:
        result['can_transfer'] = any([
            user.is_staff,
            user.is_superuser,
            hasattr(obj, "created_by") and obj.created_by == user,
        ])
        # And We have a "duplicate all" command for Category objects.
        result['is_category'] = isinstance(obj, Category)
    return result


@register.inclusion_tag("goals/_modified.html")
def modified(obj):
    """Render created/udpated on/by information for the given object. This
    assumes the object has the following attributes:

    * created_by: A User instance.
    * created_on: A Datetime field
    * updated_by: A User instance.
    * updated_on: A Datetime field

    """
    return {"obj": obj}


@register.inclusion_tag("goals/_form_buttons.html")
def form_buttons(obj, object_name=None):
    """Renders Form submit buttons. There's one required parameter: The object
    being modified (if any). This can also be None.

    Additionaly, if an object name is given, that's included
    on the Create/Save button; e.g. [Create Category]

    """
    if obj and obj.state not in ["draft", "declined"]:
        disabled = True
    else:
        disabled = False

    # We're publicly referring to actions as notifications now.
    if object_name == "Action":
        object_name = "Notification"

    return {
        "obj": obj,  # The object
        "object_name": object_name,  # The object's friendly name
        "disabled": disabled,  # Do we allow submitting for review?
    }


@register.inclusion_tag("goals/_publish_deny_form.html")
def publish_deny_form(user, obj, layout=None):
    """Given a user and and object, render the state update form
    (Draft / Publish / Deny) for the given object *if* the user has the
    appropriate permissions (i.e. 'publish' permissions or is listed as a
    package_contributor for the Category).

    You can specify optional layous by passing in a layout flag:

    * layout: "dropdown" or None are the current options.

    """
    publish_perms = {
        'category': 'goals.publish_category',
        'goal': 'goals.publish_goal',
        'behavior': 'goals.publish_behavior',
        'action': 'goals.publish_action',
    }
    if (
        user.has_perm(publish_perms.get(obj.__class__.__name__.lower())) or
        is_package_contributor(user, obj)
    ):
        return {
            "obj": obj,
            "publishable": any([obj.is_draft, obj.is_pending]),
            "declineable": any([obj.is_pending]),
            "layout": layout,
        }
    return {}
