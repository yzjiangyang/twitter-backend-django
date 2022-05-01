from datetime import timedelta
from testing.testcases import TestCase
from tweets.models import Tweet
from utils.time_helpers import utc_now


class TweetTests(TestCase):

    def test_hour_to_now(self):
        user = self.create_user('testuser')
        tweet = Tweet.objects.create(user=user, content="Good luck is coming")
        tweet.created_at = utc_now() - timedelta(hours=10)
        tweet.save()
        print(tweet.hours_to_now)
        self.assertEqual(tweet.hours_to_now, 10)