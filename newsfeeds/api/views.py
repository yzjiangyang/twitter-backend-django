from newsfeeds.api.serializers import NewsFeedSerializer
from newsfeeds.models import NewsFeed
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from utils.paginations.endless_paginations import EndlessPagination


class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = EndlessPagination
    queryset = NewsFeed.objects.all()

    def list(self, request):
        newsfeeds = NewsFeed.objects.filter(user=request.user)
        newsfeeds = self.paginate_queryset(newsfeeds)
        serializer = NewsFeedSerializer(
            newsfeeds,
            context={'request': request},
            many=True
        )
        return self.get_paginated_response(serializer.data)