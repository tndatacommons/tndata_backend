"""
This module contains utilities for generating color values from
html hex strings.


"""

def lighten(hex_color_string, lighten_by=None):
    """Given a 6-digit hex color string, #123456, this function will return
    a lighter shade of that color.

    A `lighten_by` paramter can also be specified (the default is #222222).

    """
    if lighten_by is not None:
        lighten_by = int(lighten_by.replace("#", "0x"), 16)
    else:
        lighten_by = 2236962  # 0x222222

    color_int_value = int(hex_color_string.replace("#", "0x"), 16)
    value = color_int_value + lighten_by

    # Check thresholds.
    if value > 16777215:  # max color... #ffffff
        value = color_int_value - lighten_by # subtract instead?

    value = hex(value).replace("0x", "#")

    # HACK, just add e's until we have a 6-digit color
    while len(value) < 7:
        value = value + 'e'

    return value
