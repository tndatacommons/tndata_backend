from django.test import TestCase
from .. forms import (
    ActionForm,
    BehaviorForm,
    CategoryForm,
    GoalForm,
    TriggerForm,
)
from .. models import (
    Action,
    Behavior,
    Category,
    Goal,
    Trigger,
)

from .. settings import DEFAULT_BEHAVIOR_TRIGGER_NAME


class TestActionForm(TestCase):

    def test_unbound(self):
        form = ActionForm()
        fields = sorted([
            'sequence_order', 'behavior', 'title', 'description', 'action_type',
            'more_info', 'external_resource', 'default_trigger', 'icon',
            'notification_text', 'source_link', 'source_notes', 'notes',
        ])
        self.assertEqual(fields, sorted(list(form.fields.keys())))

    def test_bound(self):
        b = Behavior.objects.create(title="asdf")
        data = {
            'sequence_order': '1',
            'behavior': b.id,
            'title': 'Some Title',
            'description': 'ASDF',
            'more_info': '',
            'external_resource': '',
            'default_trigger': '',
            'notification_text': '',
            'source_link': '',
            'source_notes': '',
            'notes': '',
            'action_type': 'custom',
        }
        form = ActionForm(data)
        self.assertTrue(form.is_valid())
        b.delete()

    def test_duplicate_title(self):
        """Ensure that duplicate titles are OK."""
        b = Behavior.objects.create(title="B")
        a = Action.objects.create(sequence_order=1, behavior=b, title="title")
        data = {
            'sequence_order': '1',
            'behavior': b.id,
            'title': 'TITLE',  # Duplicate, even tho differs by case
            'description': '',
            'more_info': '',
            'external_resource': '',
            'default_trigger': '',
            'notification_text': '',
            'icon': '',
            'source_link': '',
            'source_notes': '',
            'notes': '',
            'action_type': 'custom',
        }
        form = ActionForm(data)
        self.assertTrue(form.is_valid())
        b.delete()
        a.delete()


class TestBehaviorForm(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.trigger = Trigger.objects.create(
            name=DEFAULT_BEHAVIOR_TRIGGER_NAME,
            trigger_type="time"
        )

    def test_unbound(self):
        form = BehaviorForm()
        fields = sorted([
            'title', 'description', 'more_info', 'informal_list',
            'external_resource', 'goals', 'icon', 'source_link', 'source_notes',
             'default_trigger', 'notes',
        ])
        self.assertEqual(fields, sorted(list(form.fields.keys())))

    def test_bound(self):
        g = Goal.objects.create(title="G")
        data = {
            'title': 'New Behavior',
            'description': '',
            'more_info': '',
            'informal_list': '',
            'external_resource': '',
            'goals': [g.id],
            'icon': '',
            'default_trigger': '',
            'source_link': '',
            'source_notes': '',
            'notes': '',
        }
        form = BehaviorForm(data)
        self.assertTrue(form.is_valid())
        g.delete()

    def test_duplicate_title(self):
        """Ensure that duplicate titles fail validation."""
        g = Goal.objects.create(title="G")
        b = Behavior.objects.create(title="B")  # Existing Behavior
        data = {
            'title': 'b',  # should be a duplicate!
            'description': '',
            'more_info': '',
            'informal_list': '',
            'external_resource': '',
            'goals': [g.id],
            'icon': '',
            'default_trigger': '',
            'source_link': '',
            'source_notes': '',
            'notes': '',
        }
        form = BehaviorForm(data)
        self.assertFalse(form.is_valid())
        err = {'title': ['Behavior with this Title already exists.']}
        self.assertEqual(form.errors, err)
        b.delete()
        g.delete()


class TestCategoryForm(TestCase):

    def test_unbound(self):
        form = CategoryForm()
        fields = sorted([
            'order', 'title', 'description', 'icon', 'image', 'color', 'notes',
            'secondary_color', 'packaged_content',
        ])
        self.assertEqual(fields, sorted(list(form.fields.keys())))

    def test_bound(self):
        data = {
            'order': '1',
            'packaged_content': False,
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
        """Ensure that duplicate titles fail validation."""
        c = Category.objects.create(order=1, title="C")  # Existing object
        data = {
            'order': '2',
            'packaged_content': False,
            'title': 'c',  # Should be a Duplicate
            'description': 'asdf',
            'icon': '',
            'image': '',
            'color': '#eee',
            'notes': '',
        }
        form = CategoryForm(data)
        self.assertFalse(form.is_valid())
        err = {'title': ['Category with this Title already exists.']}
        self.assertEqual(form.errors, err)
        c.delete()


class TestGoalForm(TestCase):

    def test_unbound(self):
        form = GoalForm()
        fields = sorted([
            'categories', 'title', 'description', 'icon', 'more_info', 'notes',
        ])
        self.assertEqual(fields, sorted(list(form.fields.keys())))

    def test_bound(self):
        c = Category.objects.create(order=1, title='C')
        data = {
            'categories': [c.id],
            'title': 'New Goal',
            'description': 'asdf',
            'icon': '',
            'notes': '',
            'more_info': '',
        }
        form = GoalForm(data)
        self.assertTrue(form.is_valid())
        c.delete()

    def test_duplicate_title(self):
        """Ensure that duplicate titles fail validation."""
        c = Category.objects.create(order=1, title="C")
        g = Goal.objects.create(title='G')  # Existing object
        data = {
            'categories': [c.id],
            'title': 'g',  # Should be a duplicate
            'description': 'asdf',
            'icon': '',
            'notes': '',
        }
        form = GoalForm(data)
        self.assertFalse(form.is_valid())
        err = {'title': ['Goal with this Title already exists.']}
        self.assertEqual(form.errors, err)
        c.delete()
        g.delete()


class TestTriggerForm(TestCase):

    def test_unbound(self):
        form = TriggerForm()
        fields = sorted(['name', 'trigger_type', 'time', 'recurrences'])
        self.assertEqual(fields, sorted(list(form.fields.keys())))

    def test_bound(self):
        data = {
            'name': 'New Trigger',
            'trigger_type': 'time',
            'time': '',
            'recurrences': 'RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR',
        }
        form = TriggerForm(data)
        self.assertTrue(form.is_valid())
