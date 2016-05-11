from collections import Iterable


def flatten(values):
    """Flattens a nested list into a single list of values;

    Taken from Python Cookbook 3rd ed.

    """
    for item in values:
        if isinstance(item, Iterable):
            yield from flatten(item)
        else:
            yield item
