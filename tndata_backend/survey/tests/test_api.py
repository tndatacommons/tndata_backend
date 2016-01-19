from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from .. models import (
    BinaryQuestion,
    BinaryResponse,
    Instrument,
    LikertQuestion,
    LikertResponse,
    MultipleChoiceQuestion,
    MultipleChoiceResponse,
    MultipleChoiceResponseOption,
    OpenEndedQuestion,
    OpenEndedResponse,
)

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
}


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class TestInstrumentAPI(APITestCase):

    def setUp(self):
        self.instrument = Instrument.objects.create(title='Test Instrument')

    def tearDown(self):
        Instrument.objects.filter(id=self.instrument.id).delete()

    def test_get_list(self):
        url = reverse('instrument-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1)
        c = response.data['results'][0]
        self.assertEqual(c['id'], self.instrument.id)
        self.assertEqual(c['title'], self.instrument.title)
        self.assertEqual(c['description'], self.instrument.description)
        self.assertEqual(c['questions'], [])  # There are no questions, yet

    def test_post_list(self):
        """Ensure this endpoint is read-only."""
        url = reverse('instrument-list')
        response = self.client.post(url, {})
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_get_detail(self):
        """Ensure this endpoint provides instrument detail info."""
        url = reverse('instrument-detail', args=[self.instrument.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.instrument.id)

    def test_post_detail(self):
        """Ensure this endpoint is read-only."""
        url = reverse('instrument-detail', args=[self.instrument.id])
        response = self.client.post(url, {})
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class TestRandomQuestionAPI(APITestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create(
            username="test",
            email="test@example.com",
        )
        self.q1 = LikertQuestion.objects.create(text='Likert')
        self.q2 = OpenEndedQuestion.objects.create(text='OpenEnded')
        self.q3 = MultipleChoiceQuestion.objects.create(text='MultipleChoice')
        self.q4 = BinaryQuestion.objects.create(text='Binary')

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(id=self.user.id).delete()
        BinaryQuestion.objects.filter(id=self.q4.id).delete()
        LikertQuestion.objects.filter(id=self.q1.id).delete()
        OpenEndedQuestion.objects.filter(id=self.q2.id).delete()
        MultipleChoiceQuestion.objects.filter(id=self.q3.id).delete()

    def test_get_list_unauthorized(self):
        url = reverse('surveyrandom-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_list_authorized(self):
        url = reverse('surveyrandom-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # We should get a single object, and it should be one of our questions.
        self.assertIn("id", response.data)
        self.assertIn(
            response.data["id"],
            [self.q1.id, self.q2.id, self.q3.id, self.q4.id]
        )

    def test_get_list_authorized_filtered_by_instrument(self):
        """Ensure that the random question enpoint can filter by instrument."""
        inst = Instrument.objects.create(title="Test Instrument")
        q = BinaryQuestion.objects.create(text="Q?")
        q.instruments.add(inst)  # <-- The only question in this instrument.

        url = reverse('surveyrandom-list') + "?instrument={0}".format(inst.id)
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # We should get a single object, and it should be the instrument's question.
        self.assertIn("id", response.data)
        self.assertEqual(response.data["id"], q.id)

        # Clean up.
        q.delete()
        inst.delete()

    def test_get_list_authorized_filtered_by_invalid_instrument(self):
        """The random question enpoint returns an empty object when given an
        invalid instrument id."""

        url = reverse('surveyrandom-list') + "?instrument=99999"
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {})

    def test_post_list(self):
        """Ensure this endpoint is read-only."""
        url = reverse('surveyrandom-list')
        response = self.client.post(url, {})
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

        # Even when authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, {})
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_retrieve(self):
        """Ensure we can retrieve a single question given a combination of its
        type and id."""
        pk = "{0}-{1}".format(self.q1.question_type, self.q1.id)
        url = reverse('surveyrandom-detail', args=[pk])
        self.assertEqual(url, self.q1.get_survey_question_url())

        pk = "{0}-{1}".format(self.q2.question_type, self.q2.id)
        url = reverse('surveyrandom-detail', args=[pk])
        self.assertEqual(url, self.q2.get_survey_question_url())

        pk = "{0}-{1}".format(self.q3.question_type, self.q3.id)
        url = reverse('surveyrandom-detail', args=[pk])
        self.assertEqual(url, self.q3.get_survey_question_url())

        pk = "{0}-{1}".format(self.q4.question_type, self.q4.id)
        url = reverse('surveyrandom-detail', args=[pk])
        self.assertEqual(url, self.q4.get_survey_question_url())


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class TestBinaryQuestionAPI(APITestCase):

    def setUp(self):
        self.question = BinaryQuestion.objects.create(text='Test Question')

    def tearDown(self):
        BinaryQuestion.objects.filter(id=self.question.id).delete()

    def test_get_list(self):
        url = reverse('binaryquestion-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1)
        c = response.data['results'][0]
        self.assertEqual(c['id'], self.question.id)
        self.assertEqual(c['order'], self.question.order)
        self.assertEqual(c['text'], self.question.text)
        self.assertEqual(c['available'], self.question.available)

    def test_post_list(self):
        """Ensure this endpoint is read-only."""
        url = reverse('binaryquestion-list')
        response = self.client.post(url, {})
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_get_detail(self):
        """Ensure this endpoint provides question detail info."""
        url = reverse('binaryquestion-detail', args=[self.question.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.question.id)

    def test_post_detail(self):
        """Ensure this endpoint is read-only."""
        url = reverse('binaryquestion-detail', args=[self.question.id])
        response = self.client.post(url, {})
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class TestLikertQuestionAPI(APITestCase):

    def setUp(self):
        self.question = LikertQuestion.objects.create(text='Test Question')

    def tearDown(self):
        LikertQuestion.objects.filter(id=self.question.id).delete()

    def test_get_list(self):
        url = reverse('likertquestion-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1)
        c = response.data['results'][0]
        self.assertEqual(c['id'], self.question.id)
        self.assertEqual(c['order'], self.question.order)
        self.assertEqual(c['text'], self.question.text)
        self.assertEqual(c['available'], self.question.available)

    def test_post_list(self):
        """Ensure this endpoint is read-only."""
        url = reverse('likertquestion-list')
        response = self.client.post(url, {})
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_get_detail(self):
        """Ensure this endpoint provides question detail info."""
        url = reverse('likertquestion-detail', args=[self.question.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.question.id)

    def test_post_detail(self):
        """Ensure this endpoint is read-only."""
        url = reverse('likertquestion-detail', args=[self.question.id])
        response = self.client.post(url, {})
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class TestOpenEndedQuestionAPI(APITestCase):

    def setUp(self):
        self.question = OpenEndedQuestion.objects.create(text='Test Question')

    def tearDown(self):
        OpenEndedQuestion.objects.filter(id=self.question.id).delete()

    def test_get_list(self):
        url = reverse('openendedquestion-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1)
        c = response.data['results'][0]
        self.assertEqual(c['id'], self.question.id)
        self.assertEqual(c['order'], self.question.order)
        self.assertEqual(c['text'], self.question.text)
        self.assertEqual(c['available'], self.question.available)

    def test_post_list(self):
        """Ensure this endpoint is read-only."""
        url = reverse('openendedquestion-list')
        response = self.client.post(url, {})
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_get_detail(self):
        """Ensure this endpoint provides question detail info."""
        url = reverse('openendedquestion-detail', args=[self.question.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.question.id)

    def test_post_detail(self):
        """Ensure this endpoint is read-only."""
        url = reverse('openendedquestion-detail', args=[self.question.id])
        response = self.client.post(url, {})
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class TestMultipleChoiceQuestionAPI(APITestCase):

    def setUp(self):
        self.question = MultipleChoiceQuestion.objects.create(
            text='Test Question'
        )
        self.option = MultipleChoiceResponseOption.objects.create(
            question=self.question,
            text="Test Option",
            available=True
        )

    def tearDown(self):
        MultipleChoiceQuestion.objects.filter(id=self.question.id).delete()
        MultipleChoiceResponseOption.objects.filter(id=self.option.id).delete()

    def test_get_list(self):
        url = reverse('multiplechoicequestion-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1)
        c = response.data['results'][0]
        self.assertEqual(c['id'], self.question.id)
        self.assertEqual(c['order'], self.question.order)
        self.assertEqual(c['text'], self.question.text)
        self.assertEqual(c['available'], self.question.available)

        # Make sure the question has a list of option(s)
        self.assertIn("options", c)
        self.assertEqual(c['options'][0]['id'], self.option.id)
        self.assertEqual(c['options'][0]['text'], self.option.text)

    def test_post_list(self):
        """Ensure this endpoint is read-only."""
        url = reverse('multiplechoicequestion-list')
        response = self.client.post(url, {})
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_get_detail(self):
        """Ensure this endpoint provides question detail info."""
        url = reverse('multiplechoicequestion-detail', args=[self.question.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.question.id)
        self.assertIn("options", response.data)
        self.assertEqual(response.data['options'][0]['id'], self.option.id)
        self.assertEqual(response.data['options'][0]['text'], self.option.text)

    def test_post_detail(self):
        """Ensure this endpoint is read-only."""
        url = reverse('multiplechoicequestion-detail', args=[self.question.id])
        response = self.client.post(url, {})
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class TestBinaryResponseAPI(APITestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create(
            username="test",
            email="test@example.com",
        )
        self.question = BinaryQuestion.objects.create(text="Test Question")
        self.response = BinaryResponse.objects.create(
            user=self.user,
            question=self.question,
            selected_option=True
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(id=self.user.id).delete()
        BinaryQuestion.objects.filter(id=self.question.id).delete()
        BinaryResponse.objects.filter(id=self.response.id).delete()

    def test_get_list_unauthenticated(self):
        """Ensure un-authenticated requests don't expose any results."""
        url = reverse('binaryresponse-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_get_list_authenticated(self):
        """Ensure authenticated requests DO expose results."""
        url = reverse('binaryresponse-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.response.id)
        self.assertEqual(response.data['results'][0]['user'], self.user.id)
        self.assertEqual(
            response.data['results'][0]['question']['id'],
            self.question.id
        )

    def test_post_list_unathenticated(self):
        """Unauthenticated requests should not be allowed to post new
        BinaryResponses"""
        url = reverse('binaryresponse-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_list_athenticated(self):
        """Authenticated users should be able to create a BinaryResponse."""
        q = BinaryQuestion.objects.create(text="New Question")

        url = reverse('binaryresponse-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        data = {"question": q.id, 'selected_option': True}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BinaryResponse.objects.filter(user=self.user).count(), 2)
        q.delete()  # Clean up.

    def test_post_list_athenticated_with_string_instead_of_int(self):
        """Authenticated users should be able to create a BinaryResponse."""
        q = BinaryQuestion.objects.create(text="New Question")

        url = reverse('binaryresponse-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        data = {"question": str(q.id), 'selected_option': str(0)}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BinaryResponse.objects.filter(user=self.user).count(), 2)
        q.delete()  # Clean up.

    def test_get_detail_unauthed(self):
        """Ensure unauthenticated users cannot view this endpoint."""
        url = reverse('binaryresponse-detail', args=[self.response.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_detail(self):
        """Ensure authenticated users can view this endpoint."""
        url = reverse('binaryresponse-detail', args=[self.response.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_detail_not_allowed(self):
        """Ensure POSTing to the detail endpoint is not allowed."""
        url = reverse('binaryresponse-detail', args=[self.response.id])
        response = self.client.post(url, {'question': 1, 'selected_option': True})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Even if you're authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, {'question': 1, 'selected_option': True})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_detail_not_allowed(self):
        """Ensure PUTing to the detail endpoint is not allowed."""
        url = reverse('binaryresponse-detail', args=[self.response.id])
        response = self.client.put(url, {'question': 1, 'selected_option': True})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Even if you're authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.put(url, {'question': 1, 'selected_option': True})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_not_allowed(self):
        """Ensure DELETEing is not allowed.."""
        url = reverse('binaryresponse-detail', args=[self.response.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Even if you're authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class TestLikertResponseAPI(APITestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create(
            username="test",
            email="test@example.com",
        )
        self.question = LikertQuestion.objects.create(text="Test Question")
        self.response = LikertResponse.objects.create(
            user=self.user,
            question=self.question,
            selected_option=1
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(id=self.user.id).delete()
        LikertQuestion.objects.filter(id=self.question.id).delete()
        LikertResponse.objects.filter(id=self.response.id).delete()

    def test_get_list_unauthenticated(self):
        """Ensure un-authenticated requests don't expose any results."""
        url = reverse('likertresponse-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_get_list_authenticated(self):
        """Ensure authenticated requests DO expose results."""
        url = reverse('likertresponse-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.response.id)
        self.assertEqual(response.data['results'][0]['user'], self.user.id)
        self.assertEqual(
            response.data['results'][0]['question']['id'],
            self.question.id
        )

    def test_post_list_unathenticated(self):
        """Unauthenticated requests should not be allowed to post new
        LikertResponses"""
        url = reverse('likertresponse-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_list_athenticated(self):
        """Authenticated users should be able to create a LikertResponse."""
        q = LikertQuestion.objects.create(text="New Question")

        url = reverse('likertresponse-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        data = {"question": q.id, 'selected_option': 1}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LikertResponse.objects.filter(user=self.user).count(), 2)
        q.delete()  # Clean up.

    def test_get_detail_unauthed(self):
        """Ensure unauthenticated users cannot view this endpoint."""
        url = reverse('likertresponse-detail', args=[self.response.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_detail(self):
        """Ensure authenticated users can view this endpoint."""
        url = reverse('likertresponse-detail', args=[self.response.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_detail_not_allowed(self):
        """Ensure POSTing to the detail endpoint is not allowed."""
        url = reverse('likertresponse-detail', args=[self.response.id])
        response = self.client.post(url, {'question': 1, 'selected_option': 1})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Even if you're authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, {'question': 1, 'selected_option': 1})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_detail_not_allowed(self):
        """Ensure PUTing to the detail endpoint is not allowed."""
        url = reverse('likertresponse-detail', args=[self.response.id])
        response = self.client.put(url, {'question': 1, 'selected_option': 1})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Even if you're authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.put(url, {'question': 1, 'selected_option': 1})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_not_allowed(self):
        """Ensure DELETEing is not allowed.."""
        url = reverse('likertresponse-detail', args=[self.response.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Even if you're authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class TestOpenEndedResponseAPI(APITestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create(
            username="test",
            email="test@example.com",
        )
        self.question = OpenEndedQuestion.objects.create(text="Test Question")
        self.response = OpenEndedResponse.objects.create(
            user=self.user,
            question=self.question,
            response="Test Response"
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(id=self.user.id).delete()
        OpenEndedQuestion.objects.filter(id=self.question.id).delete()
        OpenEndedResponse.objects.filter(id=self.response.id).delete()

    def test_get_list_unauthenticated(self):
        """Ensure un-authenticated requests don't expose any results."""
        url = reverse('openendedresponse-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_get_list_authenticated(self):
        """Ensure authenticated requests DO expose results."""
        url = reverse('openendedresponse-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.response.id)
        self.assertEqual(response.data['results'][0]['user'], self.user.id)
        self.assertEqual(
            response.data['results'][0]['question']['id'],
            self.question.id
        )

    def test_post_list_unathenticated(self):
        """Unauthenticated requests should not be allowed to post new
        OpenEndedResponses"""
        url = reverse('openendedresponse-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_list_athenticated(self):
        """Authenticated users should be able to create a OpenEndedResponse."""
        q = OpenEndedQuestion.objects.create(text="New Question")

        url = reverse('openendedresponse-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        data = {"question": q.id, 'response': 7}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(OpenEndedResponse.objects.filter(user=self.user).count(), 2)
        q.delete()  # Clean up.

    def test_get_detail_unauthed(self):
        """Ensure unauthenticated users cannot view this endpoint."""
        url = reverse('openendedresponse-detail', args=[self.response.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_detail(self):
        """Ensure authenticated users can view this endpoint."""
        url = reverse('openendedresponse-detail', args=[self.response.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_detail_not_allowed(self):
        """Ensure POSTing to the detail endpoint is not allowed."""
        url = reverse('openendedresponse-detail', args=[self.response.id])
        response = self.client.post(url, {'question': 1, 'response': 7})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Even if you're authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, {'question': 1, 'response': 7})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_detail_not_allowed(self):
        """Ensure PUTing to the detail endpoint is not allowed."""
        url = reverse('openendedresponse-detail', args=[self.response.id])
        response = self.client.put(url, {'question': 1, 'response': 7})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Even if you're authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.put(url, {'question': 1, 'response': 7})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_not_allowed(self):
        """Ensure DELETEing is not allowed.."""
        url = reverse('openendedresponse-detail', args=[self.response.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Even if you're authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class TestMultipleChoiceResponseAPI(APITestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create(
            username="test",
            email="test@example.com",
        )
        self.question = MultipleChoiceQuestion.objects.create(
            text="Test Question"
        )
        self.option = MultipleChoiceResponseOption.objects.create(
            question=self.question,
            text="Option 1",
            available=True,
        )
        self.response = MultipleChoiceResponse.objects.create(
            user=self.user,
            question=self.question,
            selected_option=self.option,
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(id=self.user.id).delete()
        MultipleChoiceQuestion.objects.filter(id=self.question.id).delete()
        MultipleChoiceResponse.objects.filter(id=self.response.id).delete()
        MultipleChoiceResponseOption.objects.filter(id=self.option.id).delete()

    def test_get_list_unauthenticated(self):
        """Ensure un-authenticated requests don't expose any results."""
        url = reverse('multiplechoiceresponse-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_get_list_authenticated(self):
        """Ensure authenticated requests DO expose results."""
        url = reverse('multiplechoiceresponse-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.response.id)
        self.assertEqual(response.data['results'][0]['user'], self.user.id)
        self.assertEqual(
            response.data['results'][0]['question']['id'],
            self.question.id
        )

    def test_post_list_unathenticated(self):
        """Unauthenticated requests should not be allowed to post new
        MultipleChoiceResponses"""
        url = reverse('multiplechoiceresponse-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_list_athenticated(self):
        """Authenticated users should be able to create a
        MultipleChoiceResponse."""
        q = MultipleChoiceQuestion.objects.create(text="New Question")
        o = MultipleChoiceResponseOption.objects.create(question=q, text="A")

        url = reverse('multiplechoiceresponse-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        data = {"question": q.id, 'selected_option': o.id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            MultipleChoiceResponse.objects.filter(user=self.user).count(),
            2
        )

        # Clean up.
        q.delete()
        o.delete()

    def test_get_detail_unauthed(self):
        """Ensure unauthenticated users cannot view this endpoint."""
        url = reverse('multiplechoiceresponse-detail', args=[self.response.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_detail(self):
        """Ensure authenticated users can view this endpoint."""
        url = reverse('multiplechoiceresponse-detail', args=[self.response.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_detail_not_allowed(self):
        """Ensure POSTing to the detail endpoint is not allowed."""
        url = reverse('multiplechoiceresponse-detail', args=[self.response.id])
        data = {'question': 1, 'selected_option': self.option.id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Even if you're authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        data = {'question': 1, 'selected_option': self.option.id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_detail_not_allowed(self):
        """Ensure PUTing to the detail endpoint is not allowed."""
        url = reverse('multiplechoiceresponse-detail', args=[self.response.id])
        data = {'question': 1, 'selected_option': self.option.id}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Even if you're authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        data = {'question': 1, 'selected_option': self.option.id}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_not_allowed(self):
        """Ensure DELETEing is not allowed.."""
        url = reverse('multiplechoiceresponse-detail', args=[self.response.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Even if you're authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
