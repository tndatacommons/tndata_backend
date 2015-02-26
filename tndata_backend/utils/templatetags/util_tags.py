from django import template


register = template.Library()


@register.inclusion_tag("utils/_object_controls.html")
def object_controls(obj, label=None):
    """Renders a dropdown button with `Update` and `Delete` Links for the given
    object. Include an optional label for multiple controls on different types
    of objects. If label is omitted, the object's class name is used.

    NOTE: objects must implement `get_update_url` and `get_delete_url`.

    """
    if label is None:
        label = obj.__class__.__name__.lower()
    return {'label': label, 'object': obj}
