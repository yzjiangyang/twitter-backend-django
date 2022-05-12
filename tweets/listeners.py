def push_tweet_to_redis(sender, instance, created, **kwargs):
    if not created:
        return

    # avoid cycle import
    from tweets.services import TweetService
    TweetService.push_tweet_to_redis(instance)