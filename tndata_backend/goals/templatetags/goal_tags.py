from django import template
register = template.Library()


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
    if obj and obj.state != "draft":
        disabled = True
    else:
        disabled = False
    return {
        "obj": obj,  # The object
        "object_name": object_name,  # The object's friendly name
        "disabled": disabled,  # Do we allow submitting for review?
    }
