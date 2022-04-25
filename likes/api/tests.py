from rest_framework.test import APIClient
from testing.testcases import TestCase

LIKE_BASE_URL = '/api/likes/'


class LikeApiTests(TestCase):

    def setUp(self):
        self.user1 = self.create_user('testuser1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('testuser2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

    def test_tweet_like(self):
        tweet = self.create_tweet(self.user1)
        # anonymous is not allowed
        response = self.anonymous_client.post(LIKE_BASE_URL)
        self.assertEqual(response.status_code, 403)

        # get is not allowed
        response = self.user1_client.get(LIKE_BASE_URL)
        self.assertEqual(response.status_code, 405)

        # wrong content type
        response = self.user1_client.post(LIKE_BASE_URL, {
            'content_type': 'wrong_type',
            'object_id': tweet.id
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('errors' in response.data, True)

        # wrong id
        response = self.user1_client.post(LIKE_BASE_URL, {
            'content_type': 'tweet',
            'object_id': -1
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['errors']['object_id'][0],
            'Object does not exist'
        )

        # post successfully
        response = self.user1_client.post(LIKE_BASE_URL, {
            'content_type': 'tweet',
            'object_id': tweet.id
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.user1.id)

        # duplicated likes
        self.user1_client.post(LIKE_BASE_URL, {
            'content_type': 'tweet',
            'object_id': tweet.id
        })
        self.assertEqual(tweet.like_set.count(), 1)

        self.user2_client.post(LIKE_BASE_URL, {
            'content_type': 'tweet',
            'object_id': tweet.id
        })
        self.assertEqual(tweet.like_set.count(), 2)

    def test_comment_like(self):
        tweet = self.create_tweet(self.user1)
        comment = self.create_comment(self.user1, tweet)
        # anonymous is not allowed
        response = self.anonymous_client.post(LIKE_BASE_URL)
        self.assertEqual(response.status_code, 403)

        # get is not allowed
        response = self.user1_client.get(LIKE_BASE_URL)
        self.assertEqual(response.status_code, 405)

        # wrong content type
        response = self.user1_client.post(LIKE_BASE_URL, {
            'content_type': 'wrong_type',
            'object_id': comment.id
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('errors' in response.data, True)

        # wrong id
        response = self.user1_client.post(LIKE_BASE_URL, {
            'content_type': 'comment',
            'object_id': -1
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['errors']['object_id'][0],
            'Object does not exist'
        )

        # post successfully
        response = self.user1_client.post(LIKE_BASE_URL, {
            'content_type': 'comment',
            'object_id': comment.id
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.user1.id)

        # duplicated likes
        self.user1_client.post(LIKE_BASE_URL, {
            'content_type': 'comment',
            'object_id': comment.id
        })
        self.assertEqual(comment.like_set.count(), 1)

        self.user2_client.post(LIKE_BASE_URL, {
            'content_type': 'comment',
            'object_id': comment.id
        })
        self.assertEqual(comment.like_set.count(), 2)