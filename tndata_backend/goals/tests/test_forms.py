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


class TestActionForm(TestCase):

    def test_unbound(self):
        form = ActionForm()
        fields = sorted([
            'sequence_order', 'behavior', 'title', 'description',
            'more_info', 'external_resource', 'default_trigger',
            'notification_text', 'icon', 'source_link', 'source_notes', 'notes',
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
            'icon': '',
            'source_link': '',
            'source_notes': '',
            'notes': '',
        }
        form = ActionForm(data)
        self.assertTrue(form.is_valid())
        b.delete()

    def test_duplicate_title(self):
        """Ensure that duplicate titles fail validation."""
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
        }
        form = ActionForm(data)
        self.assertFalse(form.is_valid())
        err = {'title': ['Action with this Title already exists.']}
        self.assertEqual(form.errors, err)
        b.delete()
        a.delete()


class TestBehaviorForm(TestCase):

    def test_unbound(self):
        form = BehaviorForm()
        fields = sorted([
            'title', 'description', 'more_info', 'informal_list',
            'external_resource', 'goals', 'icon', 'source_link', 'source_notes',
            'notes',
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
        ])
        self.assertEqual(fields, sorted(list(form.fields.keys())))

    def test_bound(self):
        data = {
            'order': '1',
            'title': 'New Category',
            'description': 'asdf',
            'icon': '',
            'image': '',
            'color': '#eee',
            'notes': '',
        }
        form = CategoryForm(data)
        self.assertTrue(form.is_valid())


    def test_duplicate_title(self):
        """Ensure that duplicate titles fail validation."""
        c = Category.objects.create(order=1, title="C")  # Existing object
        data = {
            'order': '2',
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
            'categories', 'title', 'description', 'icon', 'notes',
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
