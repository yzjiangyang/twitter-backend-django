from django.utils.decorators import method_decorator
from inbox.api.serializers import (
    NotificationSerializer,
    NotificationSerializerForUpdate
)
from notifications.models import Notification
from ratelimit.decorators import ratelimit
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utils.decorators import required_param


class NotificationViewSet(viewsets.GenericViewSet, viewsets.mixins.ListModelMixin):
    # viewsets.mixins.ListModelMixin implement list api
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ('unread', )

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(methods=['GET'], detail=False, url_path='unread-count')
    @method_decorator(ratelimit(key='user', rate='3/s', method='GET', block=True))
    def unread_count(self, request):
        unread_count = self.get_queryset().filter(unread=True).count()

        return Response({'unread_count': unread_count})

    @action(methods=['POST'], detail=False, url_path='mark-all-as-read')
    @method_decorator(ratelimit(key='user', rate='3/s', method='POST', block=True))
    def mark_all_as_read(self, request):
        updated_count = self.get_queryset().\
            filter(unread=True).\
            update(unread=False)

        return Response({'marked_count': updated_count})

    @required_param(method='PUT', params=['unread'])
    @method_decorator(ratelimit(key='user', rate='3/s', method='PUT', block=True))
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = NotificationSerializerForUpdate(
            instance=instance,
            data=request.data
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Please check your input.'
            }, status=status.HTTP_400_BAD_REQUEST)
        notification = serializer.save()

        return Response(NotificationSerializer(notification).data)