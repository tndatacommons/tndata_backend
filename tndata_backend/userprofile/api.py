from django.contrib.auth import get_user_model
from rest_framework import serializers, viewsets


# Serializers define API representation
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'is_staff')


# ViewSets define the view behavior
class UserViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
