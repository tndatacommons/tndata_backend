import logging
import sys
import traceback

from decimal import Decimal
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import logout
from django.core.cache import cache
from django.db.models import F
from django.utils.text import slugify

from rest_framework import mixins, status, viewsets
from rest_framework.authentication import (
    SessionAuthentication,
    TokenAuthentication
)
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view, list_route
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from utils.mixins import VersionedViewSetMixin
from utils.oauth import verify_token
from utils.user_utils import get_client_ip, username_hash

from . import models
from . import permissions
from .serializers import v1, v2


logger = logging.getLogger(__name__)


class PlaceViewSet(VersionedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for Places. See userprofile/api_docs for more info."""
    queryset = models.Place.objects.filter(primary=True)
    serializer_class_v1 = v1.PlaceSerializer
    serializer_class_v2 = v2.PlaceSerializer
    docstring_prefix = "userprofile/api_docs"


class UserPlaceViewSet(VersionedViewSetMixin,
                       mixins.CreateModelMixin,
                       mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin,
                       viewsets.GenericViewSet):
    """ViewSet for UserPlaces. See userprofile/api_docs for more info."""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.UserPlace.objects.all()
    serializer_class_v1 = v1.UserPlaceSerializer
    serializer_class_v2 = v2.UserPlaceSerializer
    docstring_prefix = "userprofile/api_docs"
    permission_classes = [permissions.IsSelf]

    def get_queryset(self):
        return self.queryset.filter(user__id=self.request.user.id)

    def _quant(self, request, field, default=None):
        assert field in ['longitude', 'latitude']
        if field in request.data:
            value = Decimal(request.data[field]).quantize(Decimal('0.0001'))
            return str(value)
        return default

    def create(self, request, *args, **kwargs):
        place = request.data.get('place')
        if place:
            place, _ = models.Place.objects.get_or_create(name=place)
            request.data['longitude'] = self._quant(request, 'longitude')
            request.data['latitude'] = self._quant(request, 'latitude')
            request.data['place'] = place.id
            request.data['user'] = request.user.id
            request.data['profile'] = request.user.userprofile.id
            return super().create(request, *args, **kwargs)
        content = {'error': "'{}' is not a valid Place".format(place)}
        return Response(content, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        up = self.get_object()
        place = request.data.get('place')
        if place:
            place, _ = models.Place.objects.get_or_create(name=place)
            request.data['place'] = place.id
        else:
            request.data['place'] = up.place.id

        request.data['longitude'] = self._quant(request, 'longitude', up.longitude)
        request.data['latitude'] = self._quant(request, 'latitude', up.latitude)
        request.data['user'] = request.user.id
        request.data['profile'] = request.user.userprofile.id
        return super().update(request, *args, **kwargs)


class UserViewSet(VersionedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for Users. See userprofile/api_docs for more info."""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = get_user_model().objects.all()
    serializer_class_v1 = v1.UserSerializer
    serializer_class_v2 = v2.UserSerializer
    docstring_prefix = "userprofile/api_docs"
    permission_classes = [permissions.IsSelf]

    def get_queryset(self):
        qs = self.queryset.select_related("userprofile", "auth_token")
        qs = qs.filter(id=self.request.user.id)
        return qs

    @list_route(methods=['get', 'post'], url_path='oauth')
    def oauth_create(self, request, pk=None):
        """GET: List the current user's profile / google details.

        POST: Create the user if they don't already exist and return their
        profile details. The POST payload should include the following:

            {
                'email': '...',
                'first_name': '...',
                'last_name': '...',
                'image_url': '...',
                'oauth_token': '...',
            }

        Of the above values, the `email` and `oauth_token` fields are required.

        """
        content = {}
        authed = request.user.is_authenticated()
        user = request.user if authed else None
        result_status = status.HTTP_200_OK

        # Not authenticated, return empty list.
        if not authed and request.method == 'GET':
            return Response(content, status=result_status)

        # Not authenticated & this is a POST: get or create the user.
        elif not authed and request.method == "POST":
            User = get_user_model()
            try:
                data = request.data

                # Verify the given token info: https://goo.gl/MIKN9X
                token = verify_token(data.get('oauth_token'))
                if token is None:
                    return Response(
                        data={'error': 'Invalid auth token'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Note: email + (a verified) token serves as username + password.
                email = data.get('email').strip().lower()

                # XXX This is a hack to keep these users from getting the
                # XXX `selected_by_default` content from the `goals` app.
                # XXX We *must* set this before we craete the user, hence the
                # XXX use of the email in the key.
                _key = "omit-default-selections-{}".format(slugify(email))
                cache.set(_key, True, 30)

                # XXX The only unique thing about user accounts is email.
                created = False
                try:
                    user = User.objects.get(email__iexact=email)
                except User.DoesNotExist:
                    user = User.objects.create(
                        email=email,
                        username=username_hash(email)
                    )
                    created = True

                # Update the Profile fields.
                profile = user.userprofile
                profile.google_token = token  # This will change periodically
                profile.google_image = data.get('image_url', '')
                profile.app_logins += 1
                if created:
                    # Save the IP address on the user's profile
                    try:
                        profile.ip_address = get_client_ip(request)
                    except:  # XXX: Don't let any exception prevent signup.
                        pass
                profile.save()

                # Update user fields.
                if not user.username:
                    user.username = username_hash(email)
                user.first_name = data.get('first_name', '')
                user.last_name = data.get('last_name', '')
                user.is_active = True  # Auto-activate accounts from Google
                user.save()

                if created:
                    result_status = status.HTTP_201_CREATED
                else:
                    result_status = status.HTTP_200_OK
            except Exception as err:
                # Log the traceback.
                exc_type, exc_value, exc_traceback = sys.exc_info()
                tb = traceback.format_exception(exc_type, exc_value, exc_traceback)
                tb_string = "{}\n".format("\n".join(tb))
                logger.error(tb_string)

                return Response(
                    data={'error': '{}'.format(err)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if user:
            content = {
                'id': user.id,
                'profile_id': user.userprofile.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'google_image': user.userprofile.google_image,
                'google_token': user.userprofile.google_token,
                'phone': user.userprofile.phone,
                'token': user.auth_token.key,
                'needs_onboarding': user.userprofile.needs_onboarding,
            }
        return Response(content, status=result_status)

    def create(self, request, *args, **kwargs):
        """Handle the optional username/email scenario and include an Auth
        token for the API in the returned response.
        """
        # We typically expect an email address to be given, here, but this api
        # also supports a username. If we receive a username, but no email
        # address, we'll check to see if we should swap them, which may prevent
        # an edge case where we might end up with duplicate accounts.
        username = request.data.get('username')
        if username:
            username = username.lower()
            request.data['username'] = username

        email = request.data.get('email')
        if email:
            email = email.lower()
            request.data['email'] = email

        if email is None and username is not None and '@' in username:
            request.data['email'] = username
            request.data.pop('username')

        resp = super(UserViewSet, self).create(request, *args, **kwargs)

        # Include the newly-created User's auth token (if we have a user)
        if hasattr(self, 'object') and hasattr(self.object, 'auth_token'):
            resp.data['token'] = self.object.auth_token.key

        # Save the IP address on the user's profile
        try:
            uid = resp.data.get('userprofile_id')
            userprofile = models.UserProfile.objects.get(pk=uid)
            userprofile.ip_address = get_client_ip(request)
            userprofile.save()
        except:  # XXX: Don't let any exception prevent user signup.
            pass
        return resp


class UserDataViewSet(VersionedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for User Data. See userprofile/api_docs for more info."""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = get_user_model().objects.all()
    serializer_class_v1 = v1.UserDataSerializer
    serializer_class_v2 = v2.UserDataSerializer
    docstring_prefix = "userprofile/api_docs"
    permission_classes = [permissions.IsSelf]

    def get_queryset(self):
        qs = self.queryset.select_related("userprofile", "auth_token")
        qs = qs.filter(id=self.request.user.id)
        return qs


class UserFeedViewSet(VersionedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for the Feed. See userprofile/api_docs for more info."""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = get_user_model().objects.all()
    serializer_class_v1 = v1.UserFeedSerializer
    serializer_class_v2 = v2.UserFeedSerializer
    docstring_prefix = "userprofile/api_docs"
    permission_classes = [permissions.IsSelf]

    def get_queryset(self):
        return self.queryset.filter(id=self.request.user.id)


class UserAccountViewSet(VersionedViewSetMixin, viewsets.ModelViewSet):
    """The User's account info. See userprofile/api_docs for more info"""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = get_user_model().objects.all()
    serializer_class_v1 = v1.UserAccountSerializer
    serializer_class_v2 = v2.UserAccountSerializer
    docstring_prefix = "userprofile/api_docs"
    permission_classes = [permissions.IsSelf]

    def get_queryset(self):
        return self.queryset.filter(id=self.request.user.id)


class SimpleProfileViewSet(VersionedViewSetMixin,
                           mixins.ListModelMixin,
                           mixins.RetrieveModelMixin,
                           mixins.UpdateModelMixin,
                           viewsets.GenericViewSet):
    """A simpler viewset for the UserProfile model."""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.UserProfile.objects.all()
    serializer_class_v1 = v2.SimpleProfileSerializer
    serializer_class_v2 = v2.SimpleProfileSerializer
    docstring_prefix = "userprofile/api_docs"
    permission_classes = [permissions.IsSelf]

    def get_queryset(self):
        self.queryset = super().get_queryset()
        if self.request.user.is_authenticated():
            self.queryset = self.queryset.filter(user=self.request.user)
        else:
            self.queryset = self.queryset.none()
        return self.queryset

    def update(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        return super().update(request, *args, **kwargs)


class UserProfileViewSet(VersionedViewSetMixin,
                         mixins.ListModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         viewsets.GenericViewSet):
    """The User's account info. See userprofile/api_docs for more info"""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.UserProfile.objects.all()
    serializer_class_v1 = v1.UserProfileSerializer
    serializer_class_v2 = v2.UserProfileSerializer
    docstring_prefix = "userprofile/api_docs"
    permission_classes = [permissions.IsSelf]

    def get_queryset(self):
        return self.queryset.filter(user__id=self.request.user.id)

    def list(self, request, *args, **kwargs):
        resp = super(UserProfileViewSet, self).list(request, *args, **kwargs)
        # Hack the data to include FQDNs for the response_url item.
        for profile in resp.data['results']:
            for q in profile['bio']:
                q['response_url'] = self.request.build_absolute_uri(q['response_url'])
                q['question_url'] = self.request.build_absolute_uri(q['question_url'])
        return resp

    def retrieve(self, request, *args, **kwargs):
        resp = super(UserProfileViewSet, self).retrieve(request, *args, **kwargs)
        profile = resp.data
        for q in profile['bio']:
            q['response_url'] = self.request.build_absolute_uri(q['response_url'])
            q['question_url'] = self.request.build_absolute_uri(q['question_url'])
        return resp

    def update(self, request, *args, **kwargs):
        """Allow setting `timezone` or `needs_onboarding`.

        * timezone: A timezone string, e.g. "America/Chicago"
        * timezone: A timezone string, e.g. "America/Chicago"

        """
        if not settings.DEBUG:
            log_msg = "User %s setting timezone to %s"
            logger.info(log_msg % (request.user.id, request.data.get('timezone', None)))
        request.data['user'] = request.user.id
        return super(UserProfileViewSet, self).update(request, *args, **kwargs)


@api_view(['POST'])
def api_logout(request):
    """This view allows a user to log out via the api (note that this returns
    rest_framework Response instances), and send additional details with the
    logout request. Here's an example scenario:

        A user logs out of their device, and sends their registration_id for
        GCM along with the logout request. That request data gets bundled with
        the logout signal, to which the notifications app is subscribed, so
        that app knows to remove the user's device & queued messages.

    To implement the above scenario, the client would a POST request containing
    the following information:

        {registration_id: 'YOUR-REGISTRATION-ID'}

    Returns a 404 if the request does not contain an authenticated user. Returns
    a 200 request upon success.

    ----

    """
    if hasattr(request, "user") and request.user:
        logout(request)  # Sends the user_logged_out signal
        return Response(None, status=status.HTTP_200_OK)
    return Response(None, status=status.HTTP_404_NOT_FOUND)


class ObtainAuthorization(ObtainAuthToken):
    """Custom Authorization view that, in addition to the user's auth token
    (default for the superclass), returns some additional user information:

    * token
    * username
    * user_id
    * userprofile_id
    * first_name
    * last_name
    * full_name
    * email
    * needs_onboarding

    USAGE: Send a POST request to this view containing username/password
    data and receive a JSON-encoded response.

    """
    serializer_class = v1.AuthTokenSerializer

    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid(raise_exception=True):
                user = serializer.validated_data['user']
                token, created = Token.objects.get_or_create(user=user)

                # Update the number of times the user has logged in
                profiles = models.UserProfile.objects.filter(user=user)
                profiles.update(app_logins=F('app_logins') + 1)

                return Response({
                    'token': token.key,
                    'username': user.username,
                    'id': user.id,
                    'user_id': user.id,
                    'userprofile_id': user.userprofile.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'full_name': user.get_full_name(),
                    'email': user.email,
                    'zipcode': user.userprofile.zipcode,
                    'birthday': user.userprofile.birthday,  # TODO: serialize
                    'sex': user.userprofile.sex,
                    'gender': user.userprofile.sex,
                    'employed': user.userprofile.employed,
                    'is_parent': user.userprofile.is_parent,
                    'in_relationship': user.userprofile.in_relationship,
                    'has_degree': user.userprofile.has_degree,
                    'maximum_daily_notifications': user.userprofile.maximum_daily_notifications,
                    'needs_onboarding': user.userprofile.needs_onboarding,
                    'object_type': 'user',
                })
        except ValidationError as e:
            # Failed login attempt, record with axes
            # username = request.data.get(settings.AXES_USERNAME_FORM_FIELD, None)
            # if username is None:
                # username = request.data.get('username', None)
            # AccessLog.objects.create(
                # user_agent=request.META.get('HTTP_USER_AGENT', '<unknown>')[:255],
                # ip_address=get_ip(request),
                # username=username,
                # http_accept=request.META.get('HTTP_ACCEPT', '<unknown>'),
                # path_info=request.META.get('PATH_INFO', '<unknown>'),
                # trusted=False
            # )
            raise e
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

obtain_auth_token = ObtainAuthorization.as_view()
