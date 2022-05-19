from newsfeeds.models import NewsFeed
from newsfeeds.tasks import fanout_newsfeeds_main_task
from twitter.cache import USER_NEWSFEEDS_PATTERN
from utils.redis.redis_helper import RedisHelper


class NewsFeedService:

    @classmethod
    def fanout_to_followers(cls, tweet):
        fanout_newsfeeds_main_task.delay(tweet.id, tweet.user_id)

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