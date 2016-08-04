from django.db.models import Max


def get_max_order(model):
    """Given an instance of a Model class, query the largest existing value
    for the `order` field and add one. This is useful for pre-populating DB
    fields (e.g. goals.Category.order, survey.LikertQuestion.order, etc).

    """
    result = model.objects.aggregate(Max('order'))
    current_num = result['order__max'] or 0
    return current_num + 1


def get_object_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None


def get_model_name(obj):
    """Given an instance of a Model object, return the name (in all lower-case)
    of the Model.

    Example: `get_model_name(user) -> "user"`.

    This correctly handles the case where an object may be a deferred object.

    """
    object_type = type(obj)
    if object_type._deferred:
        object_type = object_type.__base__.__name__
    else:
        object_type = object_type.__name__
    return object_type.lower()
