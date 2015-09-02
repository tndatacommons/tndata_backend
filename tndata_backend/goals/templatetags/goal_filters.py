from django import template
from django.template.defaultfilters import filesizeformat
from django.utils.safestring import mark_safe
from goals.permissions import is_content_editor

register = template.Library()


@register.filter("is_editor")
def user_is_editor(user):
    """Return True if the user is a content editor, otherwise False.

    Handy for using in an if/else:

        {% if user|is_editor %}

    """
    return is_content_editor(user)


@register.filter("label", is_safe=True)
def label_state(obj):
    """Generate markup for a Foundation-based label using the object's current
    state. State values can be one of the following: draft, pending-review,
    declined, published. Usage example:

        {{ category.state|label }}

    """
    markup = '<span class="{0} label">{1}</span>'
    return mark_safe(markup.format(obj.state_label, obj.state_title))


@register.filter("details", is_safe=True)
def image_details(img_file):
    """Display some details for a given ImageFieldFile object. This should
    print the images width x height and filesize (friendly-formatted).

    Usage:  <p>Image Info: {{ category.icon|details }}</p>
    Result: <p>Image Info: 800x600, 45Kb</p>

    """
    w = ""
    h = ""
    size = ""

    try:
        # Make sure we have a file
        if img_file:
            w = img_file.width
            h = img_file.height
            size = filesizeformat(img_file.size)
    except (OSError, ValueError, AttributeError):
        pass
    return mark_safe("{0}x{1}, {2}".format(w, h, size))
