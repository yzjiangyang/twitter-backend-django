from newsfeeds.api.serializers import NewsFeedSerializer
from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedService
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from utils.paginations.endless_paginations import EndlessPagination


class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = EndlessPagination
    queryset = NewsFeed.objects.all()

    def list(self, request):
        cached_newsfeeds = NewsFeedService.get_cached_newsfeeds_from_redis(request.user.id)
        newsfeeds = self.paginator.get_paginated_cached_list_in_redis(
            cached_newsfeeds,
            request
        )
        if newsfeeds == None:
            queryset = NewsFeed.objects.filter(user=request.user)
            newsfeeds = self.paginate_queryset(queryset)
        serializer = NewsFeedSerializer(
            newsfeeds,
            context={'request': request},
            many=True
        )
        return self.get_paginated_response(serializer.data)