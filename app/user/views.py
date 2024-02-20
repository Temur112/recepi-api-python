'''Views for the user APiI'''

from rest_framework import generics, authentication, permissions, exceptions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

from user.serializers import (
    UserSerializer,
    AuthTokenSerializer,
)


class CreateUserView(generics.CreateAPIView):
    '''create a new user in the system'''
    serializer_class = UserSerializer


class CreateTokenView(ObtainAuthToken):
    '''Create new auth token for user'''
    serializer_class = AuthTokenSerializer
    renderer_class = api_settings.DEFAULT_RENDERER_CLASSES


class IsAuthenticatedOrNot(permissions.BasePermission):
    '''custom permission class'''

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            raise exceptions.NotAuthenticated()
        return True


class ManageUserView(generics.RetrieveUpdateAPIView):
    '''manage authenticated user'''

    serializer_class = UserSerializer
    authentication_class = [authentication.TokenAuthentication, ]
    permission_classes = [IsAuthenticatedOrNot, ]

    def get_object(self):
        '''Retrieve and return the authenticated user'''
        if self.request.user.is_authenticated:
            return self.request.user
        else:
            return None

    def check_permissions(self, request):
        """
        Check if the request should be permitted.
        Raises an appropriate exception if the request is not permitted.
        """
        if not request.user.is_authenticated:
            self.permission_denied(
                request, message=('Authentication credentials '
                                  'were not provided.')
            )
        return super().check_permissions(request)
