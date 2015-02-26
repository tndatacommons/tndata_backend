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
