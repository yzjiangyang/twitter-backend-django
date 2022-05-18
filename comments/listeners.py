from django.db.models import F
from tweets.models import Tweet

def incr_comments_count(sender, instance, created, **kwargs):
    if not created:
        return

    Tweet.objects.filter(id=instance.tweet_id).update(
        comments_count=F('comments_count') + 1
    )

def decr_comments_count(sender, instance, **kwargs):
    Tweet.objects.filter(id=instance.tweet_id).update(
        comments_count=F('comments_count') - 1
    )