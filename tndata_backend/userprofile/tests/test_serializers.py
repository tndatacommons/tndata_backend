from datetime import date
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from .. serializers import SimpleProfileSerializer


DRF_DT_FORMAT = settings.REST_FRAMEWORK['DATETIME_FORMAT']
TEST_REST_FRAMEWORK = {
    'PAGE_SIZE': 100,
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'utils.api.BrowsableAPIRendererWithoutForms',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'utils.api.NoThrottle',
    ),
    'VERSION_PARAM': 'version',
    'DEFAULT_VERSION': '1',
    'ALLOWED_VERSIONS': ['1', '2'],
    'DEFAULT_VERSIONING_CLASS': 'utils.api.DefaultQueryParamVersioning',
    'DATETIME_FORMAT': DRF_DT_FORMAT,
}


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class TestSimpleProfileSerializer(TestCase):

    def setUp(self):
        self.data = {
            'timezone': "America/New_York",
            'maximum_daily_notifications': 42,
            'needs_onboarding': False,
            'zipcode': '12345',
            'birthday': '1999-12-31',
            'sex': 'female',
            'employed': True,
            'is_parent': True,
            'in_relationship': True,
            'has_degree': True,
        }

    def test_serializer_is_valid(self):
        serializer = SimpleProfileSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())

        # verify validated data
        self.assertEqual(serializer.validated_data['timezone'], 'America/Chicago')
        self.assertEqual(
            serializer.validated_data['maximum_daily_notifications'], 42)
        self.assertEqual(serializer.validated_data['zipcode'], 12345)
        self.assertEqual(serializer.validated_data['birthday'], date(1999, 12, 31))
        self.assertEqual(serializer.validated_data['sex'], "female")
        self.assertIsTrue(serializer.validated_data['employed'])
        self.assertIsTrue(serializer.validated_data['is_parent'])
        self.assertIsTrue(serializer.validated_data['in_relationship'])
        self.assertIsTrue(serializer.validated_data['has_degree'])
