from comments.models import Comment
from django.contrib.contenttypes.models import ContentType
from notifications.models import Notification
from rest_framework.test import APIClient
from testing.testcases import TestCase
from tweets.models import Tweet

COMMENT_URL = '/api/comments/'
LIKE_URL = '/api/likes/'


class NotificationTestCase(TestCase):

    def setUp(self):
        self.user1 = self.create_user('testuser1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('testuser2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

    def test_send_tweet_likes_notification(self):
        tweet = self.create_tweet(self.user1)
        # self liked the tweet
        self.user1_client.post(LIKE_URL, {
            'object_id': tweet.id,
            'content_type': 'tweet',
        })
        self.assertEqual(Notification.objects.count(), 0)

        # different user liked the tweet
        self.user2_client.post(LIKE_URL, {
            'object_id': tweet.id,
            'content_type': 'tweet',
        })
        self.assertEqual(Notification.objects.count(), 1)

    def test_send_comment_likes_notification(self):
        tweet = self.create_tweet(self.user1)
        comment = self.create_comment(self.user1, tweet)
        # self liked the comment
        self.user1_client.post(LIKE_URL, {
            'object_id': comment.id,
            'content_type': 'comment',
        })
        self.assertEqual(Notification.objects.count(), 0)

        # different user liked the comment
        self.user2_client.post(LIKE_URL, {
            'object_id': comment.id,
            'content_type': 'comment',
        })
        self.assertEqual(Notification.objects.count(), 1)

    def test_send_new_comments_notification(self):
        tweet = self.create_tweet(self.user1)
        # self commented
        self.user1_client.post(COMMENT_URL, {
            'tweet_id': tweet.id,
            'content': 'any content',
        })
        self.assertEqual(Notification.objects.count(), 0)

        # different commented
        self.user2_client.post(COMMENT_URL, {
            'tweet_id': tweet.id,
            'content': 'any content',
        })
        self.assertEqual(Notification.objects.count(), 1)