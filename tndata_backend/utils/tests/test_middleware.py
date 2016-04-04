from django.http import HttpRequest, HttpResponse
from django.test import TestCase
from unittest.mock import MagicMock, Mock, patch

from ..middleware import APIMetricsMiddleware


class TestAPIMetricsMiddleware(TestCase):
    """Smoke test of the middleware. This just creates an instance of the
    middleware object and ensures things don't blow up."""

    def test_init(self):
        mid = APIMetricsMiddleware()
        self.assertIsNone(mid._key)
        self.assertIsNone(mid._start_time)
        self.assertIsNone(mid._end_time)

    def test__get_request_key(self):
        """Ensure that the middelware generates a correctly-formated request key"""
        mid = APIMetricsMiddleware()

        # When we have a list view
        request = MagicMock(HttpRequest, path='/api/foo/')
        self.assertEquals(mid._get_request_key(request), 'api-foo')

        # When we have a detail view
        request = MagicMock(HttpRequest, path='/api/foo/12983/')
        self.assertEquals(mid._get_request_key(request), 'api-foo-detail')

        # When we're not hitting the api
        request = MagicMock(HttpRequest, path='/something-else/')
        self.assertIsNone(mid._get_request_key(request))

    def test__current_average_response_time(self):
        """Ensure current average response time is calculated correctly."""

        with patch('utils.middleware.get_r') as mock_get_r:
            # When there's not a current gauge
            mock_get_r.return_value = Mock(**{'get_gauge.return_value': None})

            # Set the _end_time & _start_time, because this method expects them.
            mid = APIMetricsMiddleware()
            mid._end_time = 3
            mid._start_time = 1

            # Expected: 3 - 1 = 2
            self.assertEqual(mid._current_average_response_time(), 2.0)

            # When there IS a current gauge
            mock_get_r.reset_mock()
            mock_get_r.return_value = Mock(**{'get_gauge.return_value': 1})
            mid = APIMetricsMiddleware()
            mid._end_time = 3
            mid._start_time = 1

            # Expected: current mock averaged with the set time (2 + 1) / 2
            self.assertEqual(mid._current_average_response_time(), 1.5)

    def test_proces_request(self):
        """Ensure the process request sets a time when we're hitting an api"""

        # When we've got a request hitting the api
        request = MagicMock(HttpRequest, path='/api/foo/')
        with patch('utils.middleware.time') as mock_time:
            mock_time.time.return_value = 1
            mid = APIMetricsMiddleware()
            mid.process_request(request)
            self.assertEquals(mid._start_time, 1)

        # When we've got a request that's NOT hitting the api
        request = MagicMock(HttpRequest, path='/foo/')
        mid = APIMetricsMiddleware()
        mid.process_request(request)
        self.assertIsNone(mid._start_time)

    def test_process_response(self):
        """Ensure we set a gauge and metric when hitting the api."""
        request = MagicMock(HttpRequest, path='/api/')
        response = MagicMock(HttpResponse)

        with patch('utils.middleware.gauge') as mock_gauge:
            with patch('utils.middleware.metric') as mock_metric:
                mid = APIMetricsMiddleware()
                mid._current_average_response_time = Mock(return_value=1.0)
                mid._key = 'api'
                mid._start_time = 1
                resp = mid.process_response(request, response)

                self.assertEqual(resp, response)
                mock_gauge.assert_called_once_with('api', 1.0)
                mock_metric.assert_called_once_with('api', category='API Metrics')
