import logging

from rest_framework import permissions, status, viewsets
from rest_framework.authentication import (
    SessionAuthentication,
    TokenAuthentication
)
from rest_framework.decorators import detail_route, list_route
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
    """TODO: docs."""
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
