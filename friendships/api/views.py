from django.contrib.auth.models import User
from friendships.api.serializers import (
    FollowingSerializer,
    FollowerSerializer,
    FollowingSerializerForCreate,
)
from friendships.models import Friendship
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from utils.paginations.paginations import FriendshipPagination


class FriendshipViewSet(viewsets.GenericViewSet):
    serializer_class = FollowingSerializerForCreate
    queryset = User.objects.all()
    pagination_class = FriendshipPagination

    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    def followings(self, request, pk):
        friendships = Friendship.objects.filter(from_user=pk).order_by('-created_at')
        page = self.paginate_queryset(friendships)
        serializer = FollowingSerializer(
            page,
            context={'request': request},
            many=True
        )

        return self.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    def followers(self, request, pk):
        friendships = Friendship.objects.filter(to_user=pk).order_by('-created_at')
        page = self.paginate_queryset(friendships)
        serializer = FollowerSerializer(
            page,
            context={'request': request},
            many=True
        )

        return self.get_paginated_response(serializer.data)

    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    def follow(self, request, pk):
        user_to_follow = self.get_object()
        serializer = FollowingSerializerForCreate(data={
            'from_user_id': request.user.id,
            'to_user_id': user_to_follow.id
        })
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Please check input.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        friendship = serializer.save()
        return Response(
            FollowingSerializer(friendship, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    def unfollow(self, request, pk):
        user_to_unfollow = self.get_object()
        if request.user.id == user_to_unfollow.id:
            return Response({
                'success': False,
                'message': 'You cannot unfollow yourself.'
            }, status=status.HTTP_400_BAD_REQUEST)

        deleted, _ = Friendship.objects.filter(
            from_user=request.user,
            to_user=user_to_unfollow
        ).delete()
        return Response({'success': True, 'deleted': deleted})

    def list(self, request):
        return Response({'message': 'This is friendship homepage.'})