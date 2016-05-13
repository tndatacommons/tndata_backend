import django_rq


def clear_failed():
    queue = django_rq.get_failed_queue()
    return queue.empty()


def clear_all():
    queue = django_rq.get_queue()
    return queue.empty()
