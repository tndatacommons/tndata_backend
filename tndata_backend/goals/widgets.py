from datetime import datetime
from django import forms


class TimeSelectWidget(forms.widgets.Select):
    """This custom widget displays a TimeField as a <select> element with
    options for every hour and half-hour.
    """
    def _time_choices(self):
        """Generate the options."""
        times = []
        for h in range(24):
            times.append("{0:02d}:00".format(h))
            times.append("{0:02d}:30".format(h))
        return [
            (t, datetime.strptime(t, "%H:%M").time().strftime("%-I:%M %p"))
            for t in times
        ]

    def __init__(self, attrs=None, choices=(), include_empty=False):
        super().__init__(attrs, choices)
        # Set the default choices if none are provided.
        if len(self.choices) == 0:
            self.choices = self._time_choices()
            if include_empty:
                self.choices = [("", "--------")] + self.choices

    def render(self, name, value, attrs=None, choices=()):
        # NOTE: don't set any choices here, since the super will use those
        #       defined on the class.
        # Since this is used for a TimeField, any existing value will likely be
        # a datetime.time object, so we need to convert it back to a string
        # format (because that's what's expected in our <option>'s)
        if value and not isinstance(value, str):
            value = value.strftime("%H:%M")

        return super().render(name, value, attrs, choices)
