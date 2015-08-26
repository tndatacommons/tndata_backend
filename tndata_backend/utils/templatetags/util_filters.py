from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

import markdown


register = template.Library()


@register.filter("markdown", is_safe=True)
@stringfilter
def process_markdown(text):
    """Processes the given text as markdown, and returns the marked-up text.

    Usage:

        {{ mytext|markdown }}

    """
    return mark_safe(markdown.markdown(text))



@register.filter("iconbool", is_safe=True)
def fa_icons_for_booleans(value, invert=False):
    """Given a boolean value, this filter outputs a font-awesome icon + the
    word "Yes" or "No"

    Usage:

        {{ is_widget|iconbool }}

    """
    if bool(value) and invert:
        result = '<i class="fa fa-ban"></i> No'
    elif not bool(value) and invert:
        result = '<i class="fa fa-check"></i> Yes'
    elif bool(value):
        result = '<i class="fa fa-check"></i> Yes'
    else:
        result = '<i class="fa fa-ban"></i> No'
    return mark_safe(result)
