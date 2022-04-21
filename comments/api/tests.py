from rest_framework.test import APIClient
from testing.testcases import TestCase

COMMENT_UTL = '/api/comments/'


class CommentApiTest(TestCase):

    def setUp(self):
        self.user1 = self.create_user('testuser1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)
        self.tweet = self.create_tweet(self.user1)

        self.user2 = self.create_user('testuser2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

    def test_create(self):
        # anonymous user cannot comment
        response = self.anonymous_client.post(COMMENT_UTL)
        self.assertEqual(response.status_code, 403)

        # no parameter
        response = self.user2_client.post(COMMENT_UTL)
        self.assertEqual(response.status_code, 400)

        # only content parameter
        response = self.user2_client.post(COMMENT_UTL, {'content': 'hello'})
        self.assertEqual(response.status_code, 400)

        # content too long
        response = self.user2_client.post(COMMENT_UTL, {
            'tweet_id': self.tweet.id,
            'content': '1' * 141
        })
        self.assertEqual(response.status_code, 400)

        # comment successfully
        response = self.user2_client.post(COMMENT_UTL, {
            'tweet_id': self.tweet.id,
            'content': 'any content'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['username'], 'testuser2')
        self.assertEqual(response.data['tweet_id'], self.tweet.id)
        self.assertEqual(response.data['content'], 'any content')