import logging

from django.utils.text import slugify
from rest_framework import permissions, status, viewsets
from rest_framework.authentication import (
    SessionAuthentication,
    TokenAuthentication
)
from rest_framework.decorators import list_route
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

import maya

from .models import ChatMessage
from .serializers import ChatMessageSerializer


logger = logging.getLogger(__name__)


class IsOwner(permissions.IsAuthenticated):
    """Only allow owners of an object to view/edit it."""
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class PageSizePagination(PageNumberPagination):
    """Allow specifying a `page_size` querystring param to change page size."""
    page_size_query_param = 'page_size'


class ChatMessageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ## Contents

    - <a href="#list-a-users-chat-messages">List a User's Chat Messages</a>
    - <a href="#list-a-users-unread-messages">List a user's unread messages</a>
    - <a href="#chatmessages-objects">ChatMessage objects</a>
    - <a href="#chat-room-history">Chat Room History</a>
    - <a href="#filters">Fitlers</a>

    ----

    ## List a User's Chat Messages.

    This endpoint allows you to retrieve a paginated list of `ChatMessage`
    objects that were created by the authenticated user. This endpoint is
    currently read-only.

    ## List a user's unread messages.

    You can also retrive a list of the authenticated user's unread messages
    by sending a GET request to [/api/chat/unread/](/api/chat/unread/).

    ## ChatMessage objects.

            {
                "id": 61,
                "user": 1,
                "user_username": "brad",
                "user_full_name": "Brad Montgomery",
                "room": "chat-brad-russell",
                "text": "Hi there, this is a message",
                "read": false,
                "created_on": "2017-01-04 23:10:00+0000"
            }

    `ChatMessage` objects will have the following format, where:

    - `id` is the ChatMessage object's unique ID.
    - `user` is the user id for the user the created the chat message.
    - `user_username` is the author's username.
    - `user_full_name` is the author's full name.
    - `room` is the room in which the message was posted. All rooms are prefixed
      with `chat-` as a string and contain both participants IDs. Chat
      room participant IDs will always be listed in ascending order.
    - `text` is the text of the message.
    - `read` is a boolean. True means the user has seen the message, False
      means it is unread.
    - `created_on` is the date on which the message was persisted to the database.

    ## Chat Room History

    You can also retrive the entire history for a given chat room at
    [/api/chat/history/](/api/chat/history), with two restrictions:

    1. You must provide the exact name of the chat room as a GET parameter,
       e.g.  `/api/chat/history/?room=chat-user_a-user_b`
    2. The authenticated user *must* have been a member of that chat room.

    The number of messages returned from this endpoint can be controlled with
    a `size` parameter (the default is 20). For example, the following request
    would return 10 messages from the room `chat-foo-bar`:

        /api/chat/history/?room=chat-foo-bar&size=10

    ## Marking messages as read.

    Send a PUT request with the following payload:

        {
            room: 'chat-1-42',
        }

    This will update all messages in which the authenticated user was a
    recipient, setting them as `read`.

    ## Filters

    - `since`: Retrieve all chat messages that have been created since a given
      date/time.
    - `before`: Retrieve all chat messages that were created _before_ the given
      date/time.


    ----

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = ChatMessage.objects.all()
    serializer_class = ChatMessageSerializer
    permission_classes = [IsOwner]
    pagination_class = PageSizePagination

    def get_queryset(self):
        self.queryset = super().get_queryset().filter(user=self.request.user)
        return self.queryset

    @list_route(methods=['get'], url_path='unread')
    def unread(self, request, pk=None):
        """List the current user's unread chat messages."""
        if not request.user.is_authenticated():
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)

        messages = ChatMessage.objects.filter(
            read=False,
            room__icontains=request.user.id,
        )
        content = {
            'count': messages.count(),
            'results': ChatMessageSerializer(messages, many=True).data,
        }
        return Response(content, status=status.HTTP_200_OK)

    @list_route(methods=['get'], url_path='history')
    def chat_room_history(self, request, pk=None):
        """List some messages for the given room, with some restrictions:

        1. The room name is provided as a GET param, e.g. (?room=whatever)
        2. The authenticated user must have been a member of the room.

        Available filters:

        - room: (required) The room slug to pull history for
        - since: Get history after the give date or datetime.
        - before: Get history before the give date or datetime.
        - size: Number of messages to retrieve (default is 20)

        """
        if not request.user.is_authenticated():
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)

        # Pull all supported filters from the query params.
        room = request.query_params.get('room', None)
        size = int(request.query_params.get('size', 20))
        since = request.query_params.get('since')
        before = request.query_params.get('before')

        content = {}
        user_id = slugify(request.user.id)
        messages = ChatMessage.objects.all()

        if room and user_id in room:
            messages = messages.filter(room=room)
            if since:
                since = maya.parse(since).datetime()
                messages = messages.filter(created_on__gte=since)
            elif before:
                before = maya.parse(before).datetime()
                messages = messages.filter(created_on__lte=before)
            messages = messages[:size]

            content = {
                'count': messages.count(),
                'results': ChatMessageSerializer(messages, many=True).data,
            }
        return Response(content, status=status.HTTP_200_OK)

    @list_route(methods=['put'], url_path='read')
    def chat_room_mark_read(self, request):
        """Set the whole chat room's status as 'read'.

        1. The room name is provided in the payload, e.g. (room=whatever)
        2. The authenticated user must have been a member of the room.

        """
        if not request.user.is_authenticated():
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)

        room = request.data.get('room', None)
        user_id = slugify(request.user.id)
        if room and user_id in room:
            # We want to update messages in which the authenticated user was
            # a recipeient, so exclude any of the messages they sent
            messages = ChatMessage.objects.filter(room=room)
            messages = messages.exclude(user=request.user)
            messages.update(read=True)
            return Response(None, status=status.HTTP_204_NO_CONTENT)

        err = {
            'error': 'Either room not found or user was not a member',
        }
        return Response(err, status.HTTP_400_BAD_REQUEST)
