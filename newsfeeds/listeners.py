def push_newsfeed_to_redis(sender, instance, created, **kwargs):
    if not created:
        return

    from newsfeeds.services import NewsFeedService
    NewsFeedService.push_newsfeeds_to_redis(instance)