"""
Badgify Recipes.

See: https://github.com/ulule/django-badgify

----


Typical workflow for best performances

$ python manage.py badgify_sync badges
$ python manage.py badgify_sync awards --disable-signals
$ python manage.py badgify_sync counts


----

TODO: Ideas for implementing this:

1. Create recipes as part of the goals app.
2. Cron jobs taht will run the badgify_sync commands to do awards
3. ^ listen for signals (Award.post_save?) and send a push notification when
   a user is awarded a badge. (wrap this in a waffle.switch)
4. New app (badge_api?) that exposes a user's awarded badges

----

"""
from django.contrib.staticfiles.storage import staticfiles_storage

from badgify.recipe import BaseRecipe
import badgify

from django.contrib.auth import get_user_model
from django.utils import timezone


class PythonLoverRecipe(BaseRecipe):
    """
    A recipe class must implement:

    _ name class attribute
        The badge name (humanized).
    - image property
        The badge image/logo as a file object.

    A recipe class may implement:

    - slug class attribute
        The badge slug (used internally and in URLs). If not provided, it
        will be auto-generated based on the badge name.
    - description class attribute
        The badge description (short). It not provided, value will be blank.
    - user_ids property
        QuerySet returning User IDs likely to be awarded. You must return a
        QuerySet and not just a Python list or tuple. You can use
        values_list('id', flat=True).
    - db_read class attribute
        The database alias on which to perform read queries. Defaults to
        django.db.DEFAULT_DB_ALIAS.
    - batch_size class attribute
        How many Award objects to create at once. Defaults to
        BADGIFY_BATCH_SIZE (500).

    """
    name = 'Python Lover'
    slug = 'python-lover'
    description = 'People loving the Python programming language'

    @property
    def image(self):
        return staticfiles_storage.open('badges/python-lovers.png')

    @property
    def user_ids(self):
        User = get_user_model()
        return User.objects.filter(pk=1).values_list("id", flat=True)


# Ideas ...
class NewUserRecipe(BaseRecipe):
    name = 'New User'
    slug = 'new-user'
    description = "Congrats! You're a new user"

    @property
    def image(self):
        return staticfiles_storage.open('badges/python-lovers.png')

    @property
    def user_ids(self):
        User = get_user_model()
        since = timezone.now()  # TODO: use a sane value
        return User.objects.filter(created_on__gte=since)


# --------------------------------------------
# Register recipes Per class
# badgify.register(PythonLoverRecipe)
# badgify.register(JSLoverRecipe)
#
# OR All at once in a list
# --------------------------------------------
badgify.register([
    PythonLoverRecipe,
    NewUserRecipe,
])
