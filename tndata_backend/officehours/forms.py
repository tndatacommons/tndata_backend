from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, HTML, Layout

from .models import Course, OfficeHours


class ContactForm(forms.Form):
    your_name = forms.CharField(max_length=256)
    email = forms.EmailField()
    phone = forms.CharField(max_length=256)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False  # Don't generate <form> tags
        self.helper.template = "mdl/uni_form.html"

        self.helper.layout = Layout(
            Field('your_name', css_class="mdl-textfield__input"),
            Field('email', css_class="mdl-textfield__input"),
            Field('phone', css_class="mdl-textfield__input"),
        )


class OfficeHoursForm(forms.ModelForm):
    class Meta:
        model = OfficeHours
        fields = ("from_time", "to_time", "days")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False  # Don't generate <form> tags
        self.helper.template = "mdl/uni_form.html"

        self.helper.layout = Layout(
            HTML("<p>WAT</p>"),
            Field('from_time', css_class="mdl-textfield__input"),
            Field('to_time', css_class="mdl-textfield__input"),
            Field('days', css_class="mdl-textfield__input"),
            # XXX: WTF Why is this not getting rendered?
            HTML(self._days_options())
        )

    def _days_options(self):
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        wrapper = '<div class="mdl-textfield mdl-js-textfield"><ul>{items}</ul></div>'
        item_html = """<li>
    <label for="office-hours-day-{day_lower}"
           class="mdl-checkbox mdl-js-checkbox mdl-js-ripple-effect">
    <input type="checkbox" id="office-hours-day-{day_lower}"
           class="mdl-checkbox__input">
    <span class="mdl-checkbox__label">{day}</span>
    </label>
</li>"""
        items = ''
        for day in days:
            items += item_html.format(day=day, day_lower=day.lower())

        return wrapper.format(items=items)


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ('name', 'start_time', 'location', 'days')
