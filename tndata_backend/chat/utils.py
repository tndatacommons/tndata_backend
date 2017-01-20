from django.utils.text import slugify


def generate_room_name(values):
    """Given an iterable of values that can either be strings or User objects,
    generate a room name."""
    values = [str(v.id) if hasattr(v, 'id') else str(v) for v in values]
    values = sorted(values)
    return slugify("chat-{}-{}".format(*values))
