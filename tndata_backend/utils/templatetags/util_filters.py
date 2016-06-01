import json

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

import markdown


register = template.Library()


@register.filter("jsarray", is_safe=True)
def to_js_array(iterable, index=None):
    """Convert the given iterable to a JavaScript array.

    For example, if `values = ['foo', 'bar', 'baz']`, the following would yield:

        {{ values|jsarray }} --> '["foo", "bar", "baz"]'

    If the given interable contains nested items, the `index` option will
    retrieve a single value from that index, e.g.:

        values = [(1, 'foo'), (2, 'bar'), (3, 'baz')]

    then:

        {{ values|jsarray:0 }} --> '[1, 2, 3]'
        {{ values|jsarray:1 }} --> '["foo", "bar", "baz"]'

    """
    if len(iterable) == 0:
        return "[]"
    if index is not None:
        iterable = [t[index] for t in iterable]
    return '{}'.format(iterable)


@register.filter("json", is_safe=True)
def to_json(value):
    """Attempt to convert the primitive value to a json string."""
    return json.dumps(value)


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
