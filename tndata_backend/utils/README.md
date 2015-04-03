utils
=====

This app is a collection of utilities and features that are either shared
among other apps or don't fit anywhere else.


Database Utilities
------------------

The `db` module contains a `get_max_order` function, that when given a Model
class, will return the largest value for an `order` column. This is useful for
generating auto-populated form fields for objects that require an ordering.


EmailAuthenticationBackend
--------------------------

This app contains an `EmailAuthenticationBackend` class that allows users
to log in with an email + password pair.


Template Tags/Filters
---------------------

This app includes a few template tags and filters.

* A `markdown` filter. This template filter allows you to process text with
  markdown. Usage: `{{ some_var|markdown }}`.
* An `object_controls` template tag. Given an instance of some model, this
  will generate a dropdown menu with Update and Delete links. This assumes
  the model has `get_update_url` and `get_delete_url` methods.


Views
-----

This app includes a simple Password Reset workflow, that implements the
following steps:

1. User enters their email address in a form.
2. The account matching the given address is deactivated, and an email is sent
   to the address with a private link to change the user's password.
3. When the user visits the link, they're given a form to set a new password.
4. Upon being set, the account is re-enabled.
