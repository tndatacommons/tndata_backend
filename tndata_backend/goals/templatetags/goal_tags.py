from django import template
register = template.Library()


@register.inclusion_tag("goals/_modified.html")
def modified(obj):
    """Render created/udpated on/by information for the given object. This
    assumes the object has the following attributes:

    * created_by: A User instance.
    * created_on: A Datetime field
    * updated_by: A User instance.
    * updated_on: A Datetime field

    """
    return {"obj": obj}
