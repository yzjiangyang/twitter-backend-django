from friendships.services import FriendshipService
from newsfeeds.models import NewsFeed
from twitter.cache import USER_NEWSFEEDS_PATTERN
from utils.redis.redis_helper import RedisHelper


class NewsFeedService:

    @classmethod
    def fanout_to_followers(cls, tweet):
        followers = FriendshipService.get_followers(tweet.user)
        newsfeeds = [
            NewsFeed(user=follower, tweet=tweet)
            for follower in followers
        ]
        newsfeeds.append(NewsFeed(user=tweet.user, tweet=tweet))
        NewsFeed.objects.bulk_create(newsfeeds)
        # bulk_create won't trigger listener
        for newsfeed in newsfeeds:
            cls.push_newsfeeds_to_redis(newsfeed)

    @classmethod
    def get_cached_newsfeeds_from_redis(cls, user_id):
        queryset = NewsFeed.objects.filter(user_id=user_id)
        key = USER_NEWSFEEDS_PATTERN.format(user_id=user_id)
        return RedisHelper.load_objects(key, queryset)

    @classmethod
    def push_newsfeeds_to_redis(cls, newsfeed):
        queryset = NewsFeed.objects.filter(user_id=newsfeed.user_id)
        key = USER_NEWSFEEDS_PATTERN.format(user_id=newsfeed.user_id)
        RedisHelper.push_object(key, newsfeed, queryset)