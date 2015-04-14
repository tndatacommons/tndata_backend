from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter("label", is_safe=True)
@stringfilter
def label_state(object_state):
    """Generate markup for a Foundation-based label using the object's current
    state. State values can be one of the following: draft, pending-review,
    declined, published. Usage example:

        {{ category.state|label }}

    """
    markup = '<span class="{0} label">{1}</span>'
    state_labels = {
        'draft': 'secondary',
        'pending-review': 'warning',
        'declined': 'alert',
        'published': 'success',
    }
    title = " ".join(object_state.title().split("-"))
    label = state_labels.get(object_state, "info")
    return mark_safe(markup.format(label, title))
