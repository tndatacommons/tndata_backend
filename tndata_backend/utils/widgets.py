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
    def _guide_id(self):
        """Generate a unique id for this widget's markdown link"""
        return slugify(uuid.uuid4())

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

    def _get_markup(self):
        guide_id = self._guide_id()
        return (
            '<div><textarea{}>\r\n{}</textarea>'
            '<div class="md-support">'
            '  <strong>*bold*</strong>, <em>_italics_</em>, '
            '  1. numbered list, * bullets'
            '<span class="pull-right">'
            '<a data-dropdown="' + guide_id + '" aria-controls="md-guide" '
            '   aria-expanded="false" data-options="align:top" '
            '   class="md-guide">Markdown</a>'
            '<div id="' + guide_id + '" data-dropdown-content '
            '     class="medium f-dropdown content" aria-hidden="true" '
            '     tabindex="-1">' + self._mardown_guide() +
            '</div></span></div></div>'
        )

    @property
    def media(self):
        css = staticfiles_storage.url("css/md-helper.css")
        return Media(css={'screen': (css, )})

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, name=name)
        return format_html(
            self._get_markup(), flatatt(final_attrs), force_text(value)
        )
