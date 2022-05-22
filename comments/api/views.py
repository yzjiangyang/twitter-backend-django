from comments.api.serializers import (
    CommentSerializer,
    CommentSerializerForCreate,
    CommentSerializerForUpdate,
)
from comments.models import Comment
from django.utils.decorators import method_decorator
from inbox.services import NotificationService
from ratelimit.decorators import ratelimit
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from utils.decorators import required_param
from utils.permissions import IsObjectOwner


class CommentViewSet(viewsets.GenericViewSet):
    serializer_class = CommentSerializerForCreate
    queryset = Comment.objects.all()
    filterset_fields = ('tweet_id',)
    # GET -> '/api/comments/' - list
    # POST -> 'api/comments/' - create
    # GET -> '/api/comments/1/' - retrieve
    # PUT -> '/api/comments/1/' - update
    # DELETE -> 'api/comments/1/ - destroy
    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        if self.action in ['update', 'destroy']:
            return [IsAuthenticated(), IsObjectOwner()]
        return [AllowAny()]

    @required_param(method='GET', params=['tweet_id'])
    @method_decorator(ratelimit(key='user_or_ip', rate='10/s', method='GET', block=True))
    def list(self, request):
        queryset = self.get_queryset()
        comments = self.filter_queryset(queryset).\
            prefetch_related('user').\
            order_by('created_at')
        # comments = Comment.objects.filter(
        #     tweet_id=request.query_params['tweet_id']
        # ).prefetch_related('user').order_by('created_at')
        serializer = CommentSerializer(
            comments,
            context={'request': request},
            many=True
        )
        return Response({'comments': serializer.data})

    @method_decorator(ratelimit(key='user', rate='10/s', method='POST', block=True))
    def create(self, request):
        serializer = CommentSerializerForCreate(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Please check your input.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        comment = serializer.save()
        NotificationService.send_comment_notification(comment)
        return Response(
            CommentSerializer(comment, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @method_decorator(ratelimit(key='user', rate='10/s', method='PUT', block=True))
    def update(self, request, *args, **kwargs):
        comment = self.get_object()
        serializer =  CommentSerializerForUpdate(
            instance = comment,
            data = self.request.data
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Please check your input.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        comment = serializer.save()
        return Response(
            CommentSerializer(comment, context={'request': request}).data
        )

    @method_decorator(ratelimit(key='user', rate='5/s', method='DELETE', block=True))
    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        deleted, _ = comment.delete()

        return Response({'success': True, 'deleted': deleted})