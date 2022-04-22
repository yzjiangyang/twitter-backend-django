from rest_framework.test import APIClient
from testing.testcases import TestCase
from tweets.models import Tweet

TWEET_LIST_API = '/api/tweets/'
TWEET_CREATE_API = '/api/tweets/'
TWEET_RETRIEVE_API = '/api/tweets/{}/'


class TweetApiTests(TestCase):

    def setUp(self):
        self.user1 = self.create_user('testuser1')
        self.tweet1 = [
            self.create_tweet(self.user1, 'user1: content{}'.format(i))
            for i in range(3)
        ]
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('testuser2')
        self.tweet2 = [
            self.create_tweet(self.user2, 'user2: content{}'.format(i))
            for i in range(2)
        ]
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

    def test_list(self):
        # missing user_id
        response = self.anonymous_client.get(TWEET_LIST_API)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'missing user_id in request.')

        # user1 tweets
        response = self.anonymous_client.get(
            TWEET_LIST_API,
            {'user_id': self.user1.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['tweets']), len(self.tweet1))
        self.assertEqual(response.data['tweets'][0]['id'], self.tweet1[2].id)
        self.assertEqual(response.data['tweets'][2]['id'], self.tweet1[0].id)

        # user2 tweets
        response = self.anonymous_client.get(
            TWEET_LIST_API,
            {'user_id': self.user2.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['tweets']), len(self.tweet2))
        self.assertEqual(response.data['tweets'][0]['id'], self.tweet2[1].id)
        self.assertEqual(response.data['tweets'][1]['id'], self.tweet2[0].id)

    def test_create(self):
        # anonymous user cannot create tweet
        response = self.anonymous_client.post(
            TWEET_CREATE_API,
            {'content': 'any content'}
        )
        self.assertEqual(response.status_code, 403)

        # content too short
        response = self.user1_client.post(
            TWEET_CREATE_API,
            {'content': 'a' * 5}
        )
        self.assertEqual(response.status_code, 400)

        # content too long
        response = self.user1_client.post(
            TWEET_CREATE_API,
            {'content': 'a' * 141}
        )
        self.assertEqual(response.status_code, 400)

        # no content
        response = self.user1_client.post(TWEET_CREATE_API)
        self.assertEqual(response.status_code, 400)

        # post successfully
        tweet_count_before = Tweet.objects.count()
        response = self.user1_client.post(
            TWEET_CREATE_API,
            {'content': 'hello world!'}
        )
        tweet_count_after = Tweet.objects.count()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['username'], 'testuser1')
        self.assertEqual(response.data['content'], 'hello world!')
        self.assertEqual(tweet_count_after, tweet_count_before + 1)

    def test_retrieve(self):
        # invalid tweet id
        url = TWEET_RETRIEVE_API.format(0)
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 404)

        # no comments
        tweet = self.create_tweet(self.user1)
        url = TWEET_RETRIEVE_API.format(tweet.id)
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['comments']), 0)

        # add comments
        self.create_comment(self.user1, tweet)
        self.create_comment(self.user2, tweet)
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['comments']), 2)
        self.assertEqual(
            response.data['comments'][0]['user']['id'],
            self.user1.id
        )
        self.assertEqual(
            response.data['comments'][1]['user']['id'],
            self.user2.id
        )