from django.db.models import F
from tweets.models import Tweet
from utils.redis.redis_helper import RedisHelper

def incr_comments_count(sender, instance, created, **kwargs):
    if not created:
        return

    Tweet.objects.filter(id=instance.tweet_id).\
        update(comments_count=F('comments_count') + 1)
    # update redis
    RedisHelper.incr_count(instance.tweet, 'comments_count')

def decr_comments_count(sender, instance, **kwargs):
    Tweet.objects.filter(id=instance.tweet_id).\
        update(comments_count=F('comments_count') - 1)
    # update redis
    RedisHelper.decr_count(instance.tweet, 'comments_count')