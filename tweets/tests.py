from datetime import timedelta
from testing.testcases import TestCase
from tweets.constants import TweetPhotoStatus
from tweets.models import Tweet, TweetPhoto
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