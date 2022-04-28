from comments.models import Comment
from django.contrib.contenttypes.models import ContentType
from notifications.models import Notification
from rest_framework.test import APIClient
from testing.testcases import TestCase
from tweets.models import Tweet

COMMENT_URL = '/api/comments/'
LIKE_URL = '/api/likes/'
UNREAD_URL = '/api/notifications/unread-count/'
MARK_ALL_AS_READ_URL = '/api/notifications/mark-all-as-read/'
NOTIFICATION_URL = '/api/notifications/'
NOTIFICATION_UPDATE_URL = '/api/notifications/{}/'


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

class NotificationApiTests(TestCase):

    def setUp(self):
        self.user1 = self.create_user('testuser1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('testuser2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

    def test_unread(self):
        tweet = self.create_tweet(self.user1)

        # anonymous not allowed
        response = self.anonymous_client.get(UNREAD_URL)
        self.assertEqual(response.status_code, 403)

        # self comment has no notification
        self.user1_client.post(COMMENT_URL, {
            'tweet_id': tweet.id,
            'content': 'any content'
        })
        response = self.user1_client.get(UNREAD_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 0)

        # user2 comment tweet
        self.user2_client.post(COMMENT_URL, {
            'tweet_id': tweet.id,
            'content': 'any content'
        })
        response = self.user1_client.get(UNREAD_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 1)

        # self like has no notification
        self.user1_client.post(LIKE_URL, {
            'object_id': tweet.id,
            'content_type': 'tweet',
        })
        response = self.user1_client.get(UNREAD_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 1)

        # user 2 like the tweet
        self.user2_client.post(LIKE_URL, {
            'object_id': tweet.id,
            'content_type': 'tweet',
        })
        response = self.user1_client.get(UNREAD_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 2)

    def test_mark_all_as_read(self):
        # anonymous not allowed
        response = self.anonymous_client.post(MARK_ALL_AS_READ_URL)
        self.assertEqual(response.status_code, 403)

        tweet = self.create_tweet(self.user1)
        self.user2_client.post(COMMENT_URL, {
            'tweet_id': tweet.id,
            'content': 'any content'
        })
        self.user2_client.post(LIKE_URL, {
            'object_id': tweet.id,
            'content_type': 'tweet'
        })

        # get is not allowed
        response = self.user1_client.get(MARK_ALL_AS_READ_URL)
        self.assertEqual(response.status_code, 405)

        # user2 cannot mark all as read
        response = self.user2_client.post(MARK_ALL_AS_READ_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['marked_count'], 0)

        # user1 can mark all as read
        response = self.user1_client.post(MARK_ALL_AS_READ_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['marked_count'], 2)
        self.assertEqual(Notification.objects.filter(unread=True).count(), 0)

    def test_list(self):
        # anonymous not allowed
        response = self.anonymous_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 403)

        tweet = self.create_tweet(self.user1)
        self.user2_client.post(COMMENT_URL, {
            'tweet_id': tweet.id,
            'content': 'any content'
        })
        self.user2_client.post(LIKE_URL, {
            'object_id': tweet.id,
            'content_type': 'tweet'
        })

        # user2 cannot get user1's notifications
        response = self.user2_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        # user1 get
        response = self.user1_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)

        # mark 1 as read
        notification = Notification.objects.filter(recipient=self.user1).first()
        notification.unread = False
        notification.save()
        response = self.user1_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)

        response = self.user1_client.get(NOTIFICATION_URL, {'unread': True})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

        response = self.user1_client.get(NOTIFICATION_URL, {'unread': False})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_update(self):
        # anonymous not allowed
        response = self.anonymous_client.put(NOTIFICATION_UPDATE_URL)
        self.assertEqual(response.status_code, 403)

        tweet = self.create_tweet(self.user1)
        self.user2_client.post(COMMENT_URL, {
            'tweet_id': tweet.id,
            'content': 'any content'
        })
        self.user2_client.post(LIKE_URL, {
            'object_id': tweet.id,
            'content_type': 'tweet'
        })

        # get first notification
        notification = Notification.objects.filter(recipient=self.user1).first()
        url = NOTIFICATION_UPDATE_URL.format(notification.id)

        # user2 cannot update
        response = self.user2_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 404)

        # user1 update to unread = False
        response = self.user1_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 200)
        response = self.user1_client.get(UNREAD_URL)
        self.assertEqual(response.data['unread_count'], 1)

        # user1 update to unread = True
        response = self.user1_client.put(url, {'unread': True})
        self.assertEqual(response.status_code, 200)
        response = self.user1_client.get(UNREAD_URL)
        self.assertEqual(response.data['unread_count'], 2)

        # cannot update other info
        response = self.user1_client.put(url, {'unread': False, 'verb': 'new'})
        self.assertEqual(response.status_code, 200)
        notification.refresh_from_db()
        self.assertNotEqual(notification.verb, 'new')