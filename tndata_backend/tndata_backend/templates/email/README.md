transactional email templates
-----------------------------

Derived from [mailgun's transactional email tempaltes](https://github.com/mailgun/transactional-email-templates/).

The `base_email` is based on the *alert.html* template, and will accept the
following context.

* `alert`: If provided, will be displayed in an orange warning at the top of
  the email message.
* `cta_link` and `cta_text`: if both are provided, will be used to create a
  Call To Action button at the bottom of the content. `cta_text is html safe`

The primary content of the template can be completed by overriding the
following content blocks:

* `title`: Used as the document's `<title>` content
* `content`: The main content of your message. Please use only basic html, here.
* `post_cta`: A block in which content following the CTA (see below) can be
  added.
* `footer`: A block for text following the main text area. Typically this would
  contain an "unsubscribe" link.
