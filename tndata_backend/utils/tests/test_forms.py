from django.test import TestCase
from ..forms import EmailForm, SetNewPasswordForm


class TestEmailForm(TestCase):

    def test_unbound(self):
        form = EmailForm()
        self.assertFalse(form.is_bound)
        self.assertEqual(list(form.fields), ['email_address'])

    def test_bound(self):
        form = EmailForm({'email_address': 'test@example.com'})
        self.assertTrue(form.is_bound)
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data,
            {'email_address': 'test@example.com'}
        )

    def test_bound_invalid(self):
        form = EmailForm({'email_address': 'test'})
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())


class TestSetNewPasswordForm(TestCase):

    def test_unbound(self):
        form = SetNewPasswordForm()
        self.assertFalse(form.is_bound)
        self.assertEqual(
            sorted(list(form.fields)),
            ['password', 'password_confirmation']
        )

    def test_bound(self):
        data = {
            'password': 'secret1234',
            'password_confirmation': 'secret1234'
        }
        form = SetNewPasswordForm(data)
        self.assertTrue(form.is_bound)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data, data)

    def test_bound_invalid(self):
        unmatched = {
            'password': 'secret1234',
            'password_confirmation': '1234lakjsdfklasdjf'
        }
        form = SetNewPasswordForm(unmatched)
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['__all__'][0],
            'Your passwords do not match.'
        )

        too_short = {
            'password': 'secret',
            'password_confirmation': 'secret'
        }
        form = SetNewPasswordForm(too_short)
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['password'][0],
            'Ensure this value has at least 8 characters (it has 6).'
        )
