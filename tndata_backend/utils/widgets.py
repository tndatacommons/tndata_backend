import uuid

from django.contrib.staticfiles.storage import staticfiles_storage
from django.forms import Media, Textarea
from django.forms.utils import flatatt
from django.template.defaultfilters import slugify
from django.utils.encoding import force_text
from django.utils.html import format_html


class TextareaWithMarkdownHelperWidget(Textarea):
    """TextArea widget with a markdown guide beneath it.

    """
    class Media:
        css = {
            'all': ('css/md-helper.css', )
        }
        # NOTE: gotta include jquery (even tho it's listed on the form),
        # otherwise the md-helper.js will get included on the page first.
        js = (
            'foundation/js/vendor/jquery.js',
            "js/md-helper.js",
        )

    def __init__(self, *args, **kwargs):
        self.warning_limit = kwargs.pop('warning_limit', None)
        super().__init__(*args, **kwargs)

    def _guide_id(self):
        """Generate a unique id for this widget's markdown link"""
        # Note: selectors need to start with a character, not a number.
        return slugify("x" + uuid.uuid4().hex)

    def _mardown_guide(self):
        """quick and dirty hack to propuate a Foundation dropdown with some
        mardown authoring guides."""

        return """
        <p><strong>Markdown</strong>: This field supports Markdown. Below are
        some examples. To learn more, see
        <a href="https://guides.github.com/features/mastering-markdown/"
            target="_blank">this guide from GitHub</a>.</p>
        <pre>Headers:

# Header 1
## Header 2
### Header 3

Formatting:

_this is italic_
**this is bold**

Unordered lists:

* Item 1
* Item 2
  * Item 2a
  * Item 2b

Ordered Lists:

1. Item 1
2. Item 2
   * Item 2a
   * Item 2b

Links:

[Display name](http://example.com)
</pre>
        """

    def _warning_markup(self):
        """If this widget was specified with a `warning_limit` keyword, we'll
        include a bit of markup in which the character count for the textarea
        will be displayed. Once the character count reaches the limit, it'll
        be highlighted.

        The technique here is to:

        1. Include data- attributes on a wrapper span that tell us the `id`
           for the textear and the `limit` value.
        2. There's a bit of jquery that will count text as the user types and
           then update the span.

        """
        if self.warning_limit is not None:
            markup = (
                '<span class="md-text-length {cls}" '
                '      data-for="{fieldid}" data-limit="{limit}">'
                'Characters: <span class="count">{textlen}</span>'
                ' / {limit}</span>'
            )
            return markup.format(
                cls='ok' if self._text_length < self.warning_limit else 'warning',
                fieldid=self.final_attrs['id'],
                textlen=self._text_length,
                limit=self.warning_limit
            )
        return ''

    def _get_markup(self):
        guide_id = self._guide_id()
        return (
            self._warning_markup() +
            '<div><textarea{}>\r\n{}</textarea>'
            '<div class="md-support">'
            '  <strong>*bold*</strong>, <em>_italics_</em>, '
            '  1. numbered list, * bullets'
            '<span class="pull-right">'
            '<a data-dropdown="' + guide_id + '" '
            '   aria-controls="' + guide_id + '" '
            '   aria-expanded="false" data-options="align:top" '
            '   class="md-guide">Markdown</a>'
            '<div id="' + guide_id + '" data-dropdown-content '
            '     class="medium f-dropdown content" aria-hidden="true" '
            '     tabindex="-1">' + self._mardown_guide() +
            '</div></span></div></div>'
        )

    def render(self, name, value, attrs=None):
        # If the warning limit is enabled, we need to compute some initial
        # values in order to render the correct markup for the warning span.
        if self.warning_limit is not None and value is None:
            self._text_length = 0
        elif self.warning_limit is not None:
            self._text_length = len(value)

        if value is None:
            value = ''
        self.final_attrs = self.build_attrs(attrs, name=name)

        return format_html(
            self._get_markup(), flatatt(self.final_attrs), force_text(value)
        )
