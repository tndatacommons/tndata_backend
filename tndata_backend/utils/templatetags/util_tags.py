from django import template
register = template.Library()


@register.inclusion_tag("utils/_object_controls.html", takes_context=True)
def object_controls(context, obj, app_label, label=None):
    """Renders a dropdown button with `Update` and `Delete` Links for the given
    object. This tag accepts the following positional arguments:

    * obj: An instance of a Model.
    * app_label: The App label (used to look up permissions)
    * label: (optional)> The label for multiple controls on different types
      of objects. If label is omitted, the object's class name is used.

    NOTE: Model objects must implement `get_update_url` and `get_delete_url`.

    """
    model_name = obj.__class__.__name__.lower()
    change_perm = "{0}.change_{1}".format(app_label, model_name)
    delete_perm = "{0}.delete_{1}".format(app_label, model_name)
    if label is None:
        label = model_name

    perms = context.get('perms',[])  # Grab the permissions from the context.
    return {
        'label': label,
        'object': obj,
        'can_update': change_perm in perms,
        'can_delete': delete_perm in perms,
    }
