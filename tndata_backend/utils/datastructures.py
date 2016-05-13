from collections import Iterable


def flatten(values, ignore_types=(str, bytes)):
    """Flattens a nested list into a single list of values;

    Taken from Python Cookbook 3rd ed.

    """
    for item in values:
        if isinstance(item, Iterable) and not isinstance(item, ignore_types):
            yield from flatten(item)
        else:
            yield item
