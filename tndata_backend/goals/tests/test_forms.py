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
        v = form.is_valid()
        self.assertTrue(form.is_valid())


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
        v = form.is_valid()
        self.assertTrue(form.is_valid())
        c.delete()


class TestTriggerForm(TestCase):

    def test_unbound(self):
        form = TriggerForm()
        fields = sorted([
            'name', 'trigger_type', 'frequency', 'time', 'date', 'location',
            'text', 'instruction',
        ])
        self.assertEqual(fields, sorted(list(form.fields.keys())))

    def test_bound(self):
        data = {
            'name': 'New Trigger',
            'trigger_type': 'time',
            'frequency': 'one-time',
            'time': '',
            'date': '',
            'location': '',
            'text': '',
            'instruction': '',
        }
        form = TriggerForm(data)
        self.assertTrue(form.is_valid())
