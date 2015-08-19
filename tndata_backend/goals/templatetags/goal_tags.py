from django import template
from goals.models import Action
from utils.templatetags.util_tags import object_controls

register = template.Library()


@register.inclusion_tag("goals/_action_creation_menu_items.html")
def action_creation_menu():
    return {'action_model': Action}


@register.inclusion_tag("utils/_object_controls.html", takes_context=True)
def goal_object_controls(context, obj):
    result = object_controls(context, obj, "goals")
    user = context.request.user

    # Kind of a hack. only editors have publish_* permissions.
    editor_perm = "goals.publish_{0}".format(obj.__class__.__name__.lower())
    is_editor = user.has_perm(editor_perm)

    # Determine if the user should have certain object permissions, such as:
    # - can_update
    # - can_delete
    # - can_duplicate

    if not is_editor and (obj.is_pending or obj.is_published):
        result['can_update'] = False
        result['can_delete'] = False
    elif not is_editor and result.get('can_update', False):
        result['can_update'] = (obj.created_by == user)
        result['can_delete'] = (obj.created_by == user)

    if obj.is_pending or obj.is_draft or obj.is_declined:
        result['can_duplicate'] = False
    else:
        result['can_duplicate'] = True

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
    return {
        "obj": obj,  # The object
        "object_name": object_name,  # The object's friendly name
        "disabled": disabled,  # Do we allow submitting for review?
    }


@register.inclusion_tag("goals/_publish_deny_form.html")
def publish_deny_form(obj):
    """Given an object, render Publish / Deny buttons."""
    return {
        "obj": obj,
        "publishable": obj.state in ['draft', 'pending-review'],
        "declineable": obj.state in ['pending-review'],
    }
