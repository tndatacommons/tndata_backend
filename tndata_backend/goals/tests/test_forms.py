from unittest.mock import Mock
from django.test import TestCase
from .. forms import (
    ActionForm,
    ActionTriggerForm,
    CategoryForm,
    EnrollmentReminderForm,
    GoalForm,
    TriggerForm,
)
from .. models import (
    Action,
    Category,
    Goal,
)
from .. widgets import TimeSelectWidget


class TestActionTriggerForm(TestCase):

    def test_unbound(self):
        form = ActionTriggerForm()
        fields = sorted([
            'start_when_selected', 'stop_on_complete', 'time', 'trigger_date',
            'relative_value', 'relative_units', 'recurrences',
            'time_of_day', 'frequency',
        ])
        self.assertEqual(fields, sorted(list(form.fields.keys())))

    def test_bound_all(self):
        data = {
            'time': '6:30',
            'trigger_date': '08/20/2015',
            'recurrences': 'RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR',
            'start_when_selected': False,
            'stop_on_complete': False,
            'relative_value': 0,
            'relative_units': '',
        }
        form = ActionTriggerForm(data)
        self.assertTrue(form.is_valid())

    def test_bound_recurrence(self):
        data = {
            'time': '15:30',
            'trigger_date': '',
            'recurrences': 'RRULE:FREQ=DAILY',
            'start_when_selected': False,
            'stop_on_complete': False,
            'relative_value': 0,
            'relative_units': '',
        }
        form = ActionTriggerForm(data)
        self.assertTrue(form.is_valid())

    def test_bound_once(self):
        data = {
            'time': '7:00',
            'trigger_date': '02/01/2010',
            'recurrences': 'RRULE:FREQ=DAILY',
            'start_when_selected': False,
            'stop_on_complete': False,
            'relative_value': 0,
            'relative_units': '',
        }
        form = ActionTriggerForm(data)
        self.assertTrue(form.is_valid())

    def test_clean_relative(self):
        """Both relative values/units are required for relative triggers."""
        # When invalid
        data = {
            'time': '7:00',
            'trigger_date': '02/01/2010',
            'recurrences': 'RRULE:FREQ=DAILY',
            'start_when_selected': False,
            'stop_on_complete': False,
            'relative_value': 42,  # <-- a non-zero value
            'relative_units': '',  # <-- empty! (error)
        }
        form = ActionTriggerForm(data)
        self.assertFalse(form.is_valid())
        expected = (
            '<ul class="errorlist"><li>Both a value and units are required for '
            'Relative Reminders</li></ul>'
        )
        actual = str(form.errors['relative_value'])
        self.assertEqual(actual, expected)

        # When valid
        data['relative_units'] = 'days'
        form = ActionTriggerForm(data)
        self.assertTrue(form.is_valid())

    def test_clean_count_require_start_date(self):
        """A recurrance with a COUNT requires a start date."""
        data = {
            'time': '7:00',
            'trigger_date': '',
            'recurrences': 'RRULE:FREQ=DAILY;COUNT=2',
            'stop_on_complete': False,
            'start_when_selected': False,
            'relative_value': '0',
            'relative_units': '',
        }
        form = ActionTriggerForm(data)
        self.assertFalse(form.is_valid())
        expected = (
            '<ul class="errorlist"><li>A Trigger Date is required for '
            'recurrences that occur a set number of times</li></ul>'
        )
        actual = str(form.errors['trigger_date'])
        self.assertEqual(actual, expected)

    def test_clean_intervals_require_start_date(self):
        """A recurrance with an INTERVAL requires a start date."""
        # When invalid
        data = {
            'time': '7:00',
            'trigger_date': '',
            'recurrences': 'RRULE:FREQ=DAILY;INTERVAL=2',
            'start_when_selected': False,
            'stop_on_complete': False,
            'relative_value': '0',
            'relative_units': '',
        }
        form = ActionTriggerForm(data)
        self.assertFalse(form.is_valid())
        expected = (
            '<ul class="errorlist"><li>A Trigger Date is required for '
            'recurrences that contain an interval (such as every 2 days)'
            '</li></ul>'
        )
        actual = str(form.errors['trigger_date'])
        self.assertEqual(actual, expected)

    def test_clean_intervals_start_when_selected(self):
        """INTERVAL recurrences are valid when start_when_selected is chosen."""
        data = {
            'time': '7:00',
            'trigger_date': '',
            'recurrences': 'RRULE:FREQ=DAILY;INTERVAL=2',
            'start_when_selected': True,
            'stop_on_complete': False,
            'relative_value': '0',
            'relative_units': '',
        }
        form = ActionTriggerForm(data)
        self.assertTrue(form.is_valid())

    def test_clean_count_start_when_selected(self):
        """COUNT recurrences are valid when start_when_selected is chosen."""
        data = {
            'time': '7:00',
            'trigger_date': '',
            'recurrences': 'RRULE:FREQ=DAILY;COUNT=2',
            'start_when_selected': True,
            'stop_on_complete': False,
            'relative_value': '0',
            'relative_units': '',
        }
        form = ActionTriggerForm(data)
        self.assertTrue(form.is_valid())


class TestActionForm(TestCase):

    def test_unbound(self):
        form = ActionForm()
        fields = sorted([
            'sequence_order', 'goals', 'title', 'description',
            'more_info', 'external_resource', 'external_resource_name',
            'icon', 'notification_text', 'source_link', 'source_notes',
            'notes', 'priority', 'action_type',
        ])
        self.assertEqual(fields, sorted(list(form.fields.keys())))

    def test_bound(self):
        goal = Goal.objects.create(title="Goal")
        data = {
            'action_type': 'showing',
            'sequence_order': '1',
            'goals': [goal.id],
            'title': 'Some Title',
            'description': 'ASDF',
            'more_info': '',
            'external_resource': '',
            'notification_text': '',
            'source_link': '',
            'source_notes': '',
            'notes': '',
            'priority': Action.LOW,
        }
        form = ActionForm(data)
        self.assertTrue(form.is_valid())
        goal.delete()

    def test_is_valid(self):
        goal = Goal.objects.create(title="Goal")
        data = {
            'action_type': 'showing',
            'sequence_order': '0',
            'goals': [goal.id],
            'title': 'X' * 256,
            'description': 'some description',
            'more_info': '',
            'external_resource': '',
            'notification_text': 'Y' * 256,
            'source_link': '',
            'source_notes': '',
            'notes': '',
            'priority': Action.LOW,
        }
        form = ActionForm(data)
        self.assertTrue(form.is_valid())
        goal.delete()

    def test_not_valid(self):
        goal = Goal.objects.create(title="Goal")
        data = {
            'action_type': 'showing',
            'sequence_order': '0',
            'goals': [goal.id],
            'title': 'X' * 512,  # TOO long
            'description': 'some description',
            'more_info': '',
            'external_resource': '',
            'notification_text': 'Y' * 512,  # TOO long
            'source_link': '',
            'source_notes': '',
            'notes': '',
            'priority': Action.LOW,
        }
        form = ActionForm(data)
        self.assertFalse(form.is_valid())
        goal.delete()

    def test_duplicate_title(self):
        """Ensure that duplicate titles are OK."""
        goal = Goal.objects.create(title="Goal")
        a = Action.objects.create(sequence_order=1, title="title")
        a.goals.add(goal)
        data = {
            'action_type': 'showing',
            'sequence_order': '1',
            'goals': [goal.id],
            'title': 'TITLE',  # Duplicate, even tho differs by case
            'description': '',
            'more_info': '',
            'external_resource': '',
            'notification_text': '',
            'icon': '',
            'source_link': '',
            'source_notes': '',
            'notes': '',
            'priority': Action.LOW,
        }
        form = ActionForm(data)
        self.assertTrue(form.is_valid())
        goal.delete()
        a.delete()


class TestCategoryForm(TestCase):

    def test_unbound(self):
        form = CategoryForm()
        fields = sorted([
            'title', 'description', 'grouping', 'icon', 'image', 'color', 'notes',
            'secondary_color', 'packaged_content', 'contributors',
            'consent_summary', 'consent_more', 'prevent_custom_triggers_default',
            'display_prevent_custom_triggers_option', 'organizations',
            'hidden_from_organizations',
        ])
        self.assertEqual(fields, sorted(list(form.fields.keys())))

    def test_unboud_with_superuser(self):
        mock_user = Mock(is_superuser=True)
        form = CategoryForm(user=mock_user)
        fields = sorted([
            'title', 'description', 'icon', 'image', 'color', 'notes',
            'secondary_color', 'packaged_content', 'contributors',
            'consent_summary', 'consent_more', 'prevent_custom_triggers_default',
            'display_prevent_custom_triggers_option', 'selected_by_default',
            'grouping', 'organizations', 'hidden_from_organizations',
        ])
        self.assertEqual(fields, sorted(list(form.fields.keys())))

    def test_bound(self):
        data = {
            'packaged_content': False,
            'contributors': '',
            'title': 'New Category',
            'description': 'asdf',
            'icon': '',
            'image': '',
            'color': '#eee',
            'secondary_color': '',
            'notes': '',
        }
        form = CategoryForm(data)
        self.assertTrue(form.is_valid())

    def test_duplicate_title(self):
        """Ensure that duplicate titles now pass validation."""
        c = Category.objects.create(order=1, title="C")  # Existing object
        data = {
            'packaged_content': False,
            'contributors': '',
            'title': 'c',  # Should be a Duplicate
            'description': 'asdf',
            'icon': '',
            'image': '',
            'color': '#eee',
            'notes': '',
        }
        form = CategoryForm(data)
        self.assertTrue(form.is_valid())
        c.delete()


class TestGoalForm(TestCase):

    def test_unbound(self):
        form = GoalForm()
        fields = sorted([
            'categories', 'title', 'description', 'icon', 'more_info', 'notes',
            'keywords', 'sequence_order', 'original_goal',
        ])
        self.assertEqual(fields, sorted(list(form.fields.keys())))

    def test_bound(self):
        c = Category.objects.create(order=1, title='C')
        data = {
            'categories': [c.id],
            'title': 'New Goal',
            'sequence_order': '1',
            'description': 'asdf',
            'icon': '',
            'notes': '',
            'more_info': '',
            'original_goal': '',
        }
        form = GoalForm(data)
        self.assertTrue(form.is_valid())
        c.delete()

    def test_duplicate_title(self):
        """Ensure that duplicate titles now pass validation."""
        c = Category.objects.create(order=1, title="C")
        g = Goal.objects.create(title='G')  # Existing object
        data = {
            'categories': [c.id],
            'title': 'g',  # Should be a duplicate
            'sequence_order': '1',
            'description': 'asdf',
            'icon': '',
            'notes': '',
            'original_goal': '',
        }
        form = GoalForm(data)
        self.assertTrue(form.is_valid())
        c.delete()
        g.delete()


class TestTriggerForm(TestCase):

    def test_unbound(self):
        form = TriggerForm()
        fields = sorted(['time_of_day', 'frequency'])
        self.assertEqual(fields, sorted(list(form.fields.keys())))

    def test_bound(self):
        data = {'time_of_day': 'early', 'frequency': 'daily'}
        form = TriggerForm(data)
        self.assertTrue(form.is_valid())


class TestTimeSelectWidget(TestCase):

    def test_choices(self):
        widget = TimeSelectWidget()
        self.assertEqual(len(widget.choices), 48)  # 2 per hour

    def test_choices_include_empty(self):
        widget = TimeSelectWidget(include_empty=True)
        self.assertEqual(len(widget.choices), 49)  # 2 per hour + 1

    def test_rendered(self):
        widget = TimeSelectWidget()
        rendered = widget.render("test-widget", "")
        rendered_parts = rendered.split("\n")
        # An <option> for every time (48) + 2 (<select> and </select>)
        self.assertEqual(len(rendered_parts), 50)


class TestEnrollmentReminderForm(TestCase):

    def test_unbound(self):
        form = EnrollmentReminderForm()
        self.assertEqual(list(form.fields.keys()), ['message'])
        self.assertIn('message', form.initial)
        self.assertEqual(form.initial['message'], form._initial_message())

    def test_bound_all(self):
        data = {'message': 'Testing'}
        form = EnrollmentReminderForm(data)
        self.assertTrue(form.is_valid())
