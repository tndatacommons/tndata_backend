from rest_framework import viewsets
from rest_framework.authentication import (
    SessionAuthentication,
    TokenAuthentication
)

from .models import Award, Badge
from .permissions import IsOwner
from .serializers import AwardSerializer, BadgeSerializer


class AwardViewSet(viewsets.ReadOnlyModelViewSet):
    """List the authenticated user's awards."""
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = Award.objects.all()
    serializer_class = AwardSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return self.queryset.filter(user__id=self.request.user.id)


class BadgeViewSet(viewsets.ReadOnlyModelViewSet):
    """List all of the badges."""
    queryset = Badge.objects.all()
    serializer_class = BadgeSerializer
