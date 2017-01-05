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
      with `chat-` as a string and contain both participants username. Chat
      room usernames will always be listed in alphabetical order.
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
            room__icontains=request.user.username,
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

        """
        if not request.user.is_authenticated():
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)

        room = request.GET.get('room', None)
        size = int(request.GET.get('size', 20))
        username = slugify(request.user.username)
        content = {}
        if room and username in room:
            messages = ChatMessage.objects.filter(room=room)[:size]
            content = {
                'count': messages.count(),
                'results': ChatMessageSerializer(messages, many=True).data,
            }
        return Response(content, status=status.HTTP_200_OK)
