from newsfeeds.models import NewsFeed
from rest_framework.test import APIClient
from testing.testcases import TestCase

NEWSFEEDS_URL = '/api/newsfeeds/'
POST_TWEETS_URL = '/api/tweets/'


class NewsFeedApiTests(TestCase):

    def setUp(self):
        self.user1 = self.create_user('testuser1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('testuser2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

    def test_list(self):
        # anonymous user cannot get newsfeed
        response = self.anonymous_user.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 403)

        # post method not allowed
        response = self.user1_client.post(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 405)

        # user1 post a tweet
        self.user1_client.post(POST_TWEETS_URL, {'content': 'any content'})
        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['newsfeeds']), 1)
        self.assertEqual(
            response.data['newsfeeds'][0]['tweet']['user']['username'],
            'testuser1'
        )
        self.assertEqual(NewsFeed.objects.count(), 1)

        # user1 follow user2 and user2 post a tweet
        self.create_friendship(self.user1, self.user2)
        self.user2_client.post(POST_TWEETS_URL, {'content': 'any content'})
        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['newsfeeds']), 2)
        self.assertEqual(
            response.data['newsfeeds'][0]['tweet']['user']['username'],
            'testuser2'
        )
        self.assertEqual(NewsFeed.objects.count(), 3)