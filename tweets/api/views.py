from newsfeeds.services import NewsFeedService
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from tweets.api.serializers import (
    TweetSerializer,
    TweetSerializerForCreate,
    TweetSerializerForDetail,
)
from tweets.models import Tweet
from tweets.services import TweetService
from utils.decorators import required_param
from utils.paginations.endless_paginations import EndlessPagination


class TweetViewSet(viewsets.GenericViewSet):
    queryset = Tweet.objects.all()
    serializer_class = TweetSerializerForCreate
    pagination_class = EndlessPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    @required_param(method='GET', params=['user_id'])
    def list(self, request):
        user_id = request.query_params['user_id']
        # get tweet list from redis instead of db
        tweets = TweetService.get_cached_tweets_from_redis(user_id)
        # tweets = Tweet.objects.filter(user_id=user_id).order_by('-created_at')
        # pagination
        tweets = self.paginate_queryset(tweets)
        serializer = TweetSerializer(
            tweets,
            context={'request': request},
            many=True,
        )
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        tweet = self.get_object()
        serializer = TweetSerializerForDetail(
            tweet,
            context={'request': request}
        )
        return Response(serializer.data)

    def create(self, request):
        serializer = TweetSerializerForCreate(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Please check your input.',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        tweet = serializer.save()
        NewsFeedService.fanout_to_followers(tweet)
        return Response(
            TweetSerializer(tweet, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )