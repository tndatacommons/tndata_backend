import random
from django import template

register = template.Library()


@register.inclusion_tag("utils/_object_controls.html", takes_context=True)
def object_controls(context, obj, app_label, label=None):
    """Renders a dropdown button with `Update` and `Delete` Links for the given
    object. This tag accepts the following positional arguments:

    * obj: An instance of a Model.
    * app_label: The App label (used to look up permissions)
    * label: (optional)> The label for multiple controls on different types
      of objects. If label is omitted, the object's class name is used.

    NOTE: Model objects must implement `get_update_url` and `get_delete_url`.

    """
    model_name = obj.__class__.__name__.lower()
    change_perm = "{0}.change_{1}".format(app_label, model_name)
    delete_perm = "{0}.delete_{1}".format(app_label, model_name)
    if label is None:
        label = model_name

    perms = context.get('perms', [])  # Grab the permissions from the context.

    # To duplicate, a user must be able to create an object and the object
    # must have the appropriate api.
    create_perm = "{0}.add_{1}".format(app_label, model_name)
    can_duplicate = create_perm in perms and hasattr(obj, "get_duplicate_url")

    return {
        'label': label,
        'object': obj,
        'can_update': change_perm in perms,
        'can_delete': delete_perm in perms,
        'can_duplicate': can_duplicate,
    }


# pulled a list of colors from: http://www.computerhope.com/htmcolor.htm
blue_colors = [
    '#357EC7',  # Slate Blue
    '#368BC1',  # Glacial Blue Ice
    '#488AC7',  # Silk Blue
    '#3090C7',  # Blue Ivy
    '#659EC7',  # Blue Koi
    '#87AFC7',  # Columbia Blue
    '#95B9C7',  # Baby Blue
    '#728FCE',  # Light Steel Blue
    '#2B65EC',  # Ocean Blue
    '#306EFF',  # Blue Ribbon
    '#157DEC',  # Blue Dress
    '#1589FF',  # Dodger Blue
    '#6495ED',  # Cornflower Blue
    '#6698FF',  # Sky Blue
    '#38ACEC',  # Butterfly Blue
    '#56A5EC',  # Iceberg
    '#5CB3FF',  # Crystal Blue
    '#3BB9FF',  # Deep Sky Blue
    '#79BAEC',  # Denim Blue
    '#82CAFA',  # Light Sky Blue
    '#82CAFF',  # Day Sky Blue
    '#A0CFEC',  # Jeans Blue
    '#B7CEEC',  # Blue Angel
    '#B4CFEC',  # Pastel Blue
    '#C2DFFF',  # Sea Blue
    '#C6DEFF',  # Powder Blue
    '#AFDCEC',  # Coral Blue
    '#ADDFFF',  # Light Blue
    '#BDEDFF',  # Robin Egg Blue
    '#CFECEC',  # Pale Blue Lily
    '#E0FFFF',  # Light Cyan
    '#EBF4FA',  # Water
    '#F0F8FF',  # AliceBlue
    '#F0FFFF',  # Azure
    '#CCFFFF',  # Light Slate
]


@register.simple_tag
def random_color():
    return random.choice(blue_colors)
