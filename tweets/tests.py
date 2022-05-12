from datetime import timedelta
from testing.testcases import TestCase
from tweets.constants import TweetPhotoStatus
from tweets.models import Tweet, TweetPhoto
from tweets.services import TweetService
from twitter.cache import USER_TWEETS_PATTERN
from utils.redis.redis_client import RedisClient
from utils.redis.redis_serializers import DjangoModelSerializer
from utils.time_helpers import utc_now


class TweetTests(TestCase):

    def test_hour_to_now(self):
        user = self.create_user('testuser')
        tweet = Tweet.objects.create(user=user, content="Good luck is coming")
        tweet.created_at = utc_now() - timedelta(hours=10)
        tweet.save()
        print(tweet.hours_to_now)
        self.assertEqual(tweet.hours_to_now, 10)

    def test_upload_picture(self):
        user = self.create_user('testuser')
        tweet = self.create_tweet(user)
        photo = TweetPhoto.objects.create(user=user, tweet=tweet)
        self.assertEqual(photo.user, user)
        self.assertEqual(TweetPhoto.objects.count(), 1)
        self.assertEqual(photo.status, TweetPhotoStatus.PENDING)

    def test_cache_in_redis(self):
        user = self.create_user('testuser')
        tweet = self.create_tweet(user)

        conn = RedisClient.get_connection()
        serialized_data = DjangoModelSerializer.serialize(tweet)
        key = 'tweet:{}'.format(tweet.id)
        conn.set(key, serialized_data)
        # key not exist
        data = conn.get('wrong_key')
        self.assertEqual(data, None)
        # key exist
        data = conn.get(key)
        cached_tweet = DjangoModelSerializer.deserializer(data)
        self.assertEqual(cached_tweet, tweet)
        # clear redis cache
        RedisClient.clear()
        data = conn.get(key)
        self.assertEqual(data, None)

    def test_cached_tweet_list_in_redis(self):
        user = self.create_user('testuser')
        tweet_ids = []
        for i in range(3):
            tweet = self.create_tweet(user)
            tweet_ids.append(tweet.id)
        tweet_ids = tweet_ids[::-1]

        conn = RedisClient.get_connection()
        RedisClient.clear()

        # cache miss
        key = USER_TWEETS_PATTERN.format(user_id=user.id)
        self.assertEqual(conn.exists(key), False)
        tweets = TweetService.get_cached_tweets_from_redis(user.id)
        self.assertEqual([tweet.id for tweet in tweets], tweet_ids)
        # cache hit
        self.assertEqual(conn.exists(key), True)
        tweets = TweetService.get_cached_tweets_from_redis(user.id)
        self.assertEqual([tweet.id for tweet in tweets], tweet_ids)

        # cache updated after a new tweet is created
        new_tweet = self.create_tweet(user, 'a new tweet')
        tweets = TweetService.get_cached_tweets_from_redis(user.id)
        tweet_ids.insert(0, new_tweet.id)
        self.assertEqual([tweet.id for tweet in tweets], tweet_ids)