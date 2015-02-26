from django.db.models import Max


def get_max_order(model):
    """Given an instance of a Model class, query the largest existing value
    for the `order` field and add one. This is useful for pre-populating DB
    fields (e.g. goals.Category.order, survey.LikertQuestion.order, etc).

    """
    result = model.objects.aggregate(Max('order'))
    current_num = result['order__max'] or 0
    return current_num + 1
