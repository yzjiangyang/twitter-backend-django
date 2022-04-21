from comments.api.serializers import (
    CommentSerializer,
    CommentSerializerForCreate,
    CommentSerializerForUpdate,
)
from comments.models import Comment
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from utils.permissions import IsObjectOwner


class CommentViewSet(viewsets.GenericViewSet):
    serializer_class = CommentSerializerForCreate
    queryset = Comment.objects.all()
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
        return Response(
            CommentSerializer(comment).data,
            status=status.HTTP_201_CREATED
        )

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
        return Response(CommentSerializer(comment).data)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        deleted, _ =comment.delete()

        return Response({'success': True, 'deleted': deleted})