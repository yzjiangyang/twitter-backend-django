from celery import shared_task
from friendships.services import FriendshipService
from newsfeeds.constants import FANOUT_BATCH_SIZE
from newsfeeds.models import NewsFeed
from utils.time_constants import ONE_HOUR

@shared_task(time_limit=ONE_HOUR, routing_key='default')
def fanout_newsfeeds_main_task(tweet_id, tweet_user_id):
    # owner can see the tweet first after posting
    NewsFeed.objects.create(user_id=tweet_user_id, tweet_id=tweet_id)
    follower_ids = FriendshipService.get_follower_ids(tweet_user_id)
    index = 0
    while index < len(follower_ids):
        batch_ids = follower_ids[index: index + FANOUT_BATCH_SIZE]
        fanout_newsfeeds_batch_task.delay(tweet_id, batch_ids)
        index += FANOUT_BATCH_SIZE

    return '{} newsfeeds will be fanned out, {} batches are created'.format(
        len(follower_ids),
        (len(follower_ids) - 1) // FANOUT_BATCH_SIZE + 1
    )

@shared_task(time_limit=ONE_HOUR, routing_key='newsfeeds')
def fanout_newsfeeds_batch_task(tweet_id, follower_ids):
    newsfeeds = [
        NewsFeed(user_id=follower_id, tweet_id=tweet_id)
        for follower_id in follower_ids
    ]
    NewsFeed.objects.bulk_create(newsfeeds)
    # bulk_create won't trigger listener
    for newsfeed in newsfeeds:
        from newsfeeds.services import NewsFeedService
        NewsFeedService.push_newsfeeds_to_redis(newsfeed)

    return '{} newsfeeds are created.'.format(len(newsfeeds))