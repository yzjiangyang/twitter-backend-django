from newsfeeds.services import NewsFeedService
from testing.testcases import TestCase
from twitter.cache import USER_NEWSFEEDS_PATTERN
from utils.redis.redis_client import RedisClient


class NewsFeedServiceTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.user1 = self.create_user('testuser1')
        self.user2 = self.create_user('testuser2')

    def test_newsfeeds_list_in_redis(self):
        newsfeed_ids = []
        for i in range(3):
            tweet = self.create_tweet(self.user1)
            newsfeed = self.create_newsfeed(self.user2, tweet)
            newsfeed_ids.append(newsfeed.id)

        newsfeed_ids = newsfeed_ids[::-1]
        RedisClient.clear()
        conn = RedisClient.get_connection()

        # cache miss
        key = USER_NEWSFEEDS_PATTERN.format(user_id=self.user2.id)
        self.assertEqual(conn.exists(key), False)
        newsfeeds = NewsFeedService.get_cached_newsfeeds_from_redis(self.user2.id)
        self.assertEqual([newsfeed.id for newsfeed in newsfeeds], newsfeed_ids)

        # cache hit
        key = USER_NEWSFEEDS_PATTERN.format(user_id=self.user2.id)
        self.assertEqual(conn.exists(key), True)
        newsfeeds = NewsFeedService.get_cached_newsfeeds_from_redis(self.user2.id)
        self.assertEqual([newsfeed.id for newsfeed in newsfeeds], newsfeed_ids)

        # add a new newsfeed
        new_tweet = self.create_tweet(self.user1)
        new_newsfeed = self.create_newsfeed(self.user2, new_tweet)
        newsfeed_ids.insert(0, new_newsfeed.id)
        newsfeeds = NewsFeedService.get_cached_newsfeeds_from_redis(self.user2.id)
        self.assertEqual([newsfeed.id for newsfeed in newsfeeds], newsfeed_ids)

        # username updated
        self.user1.username = 'user1_new_name'
        self.user1.save()
        self.assertEqual(newsfeeds[0].tweet.user.username, 'user1_new_name')

        # profile updated
        user1_profile = self.user1.profile
        user1_profile.nickname = 'user1_nickname'
        user1_profile.save()
        self.assertEqual(newsfeeds[0].tweet.user.profile.nickname, 'user1_nickname')