from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from testing.testcases import TestCase
from tweets.models import Tweet, TweetPhoto
from utils.paginations.endless_paginations import EndlessPagination

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
        self.assertEqual(len(response.data['results']), len(self.tweet1))
        self.assertEqual(response.data['results'][0]['id'], self.tweet1[2].id)
        self.assertEqual(response.data['results'][2]['id'], self.tweet1[0].id)

        # user2 tweets
        response = self.anonymous_client.get(
            TWEET_LIST_API,
            {'user_id': self.user2.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), len(self.tweet2))
        self.assertEqual(response.data['results'][0]['id'], self.tweet2[1].id)
        self.assertEqual(response.data['results'][1]['id'], self.tweet2[0].id)

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

    def test_create_tweet_with_pictures(self):
        # upload empty files
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'test content',
            'files': []
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TweetPhoto.objects.count(), 0)

        # upload one picture
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'test content',
            'files': [
                SimpleUploadedFile(
                    name='test.jpeg',
                    content=str.encode('a test image'),
                    content_type='image/jpeg'
                )
            ]
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TweetPhoto.objects.count(), 1)

        # upload 2 pictures
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'test content',
            'files': [
                SimpleUploadedFile(
                    name='test{}.jpeg'.format(i),
                    content=str.encode('a test image{}'.format(i)),
                    content_type='image/jpeg'
                ) for i in range(2)
            ]
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TweetPhoto.objects.count(), 3)
        self.assertEqual('test0' in response.data['photo_urls'][0], True)
        self.assertEqual('test1' in response.data['photo_urls'][1], True)

        # test tweet retrieve, should have photos too
        url = TWEET_RETRIEVE_API.format(response.data['id'])
        response = self.user1_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['photo_urls']), 2)
        self.assertEqual('test0' in response.data['photo_urls'][0], True)
        self.assertEqual('test1' in response.data['photo_urls'][1], True)

        # upload more than the limit
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'test content',
            'files': [
                SimpleUploadedFile(
                    name='test{}.jpeg'.format(i),
                    content=str.encode('a test image{}'.format(i)),
                    content_type='image/jpeg'
                ) for i in range(10)
            ]
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(TweetPhoto.objects.count(), 3)

    def test_endless_pagination(self):
        page_size = EndlessPagination.page_size
        for i in range(page_size * 2 - len(self.tweet1)):
           self.tweet1.append(self.create_tweet(self.user1))
        tweets = self.tweet1[::-1]

        # 1st page
        response = self.user1_client.get(
            TWEET_LIST_API, {'user_id': self.user1.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_next_page'], True)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['id'], tweets[0].id)
        self.assertEqual(response.data['results'][1]['id'], tweets[1].id)
        self.assertEqual(
            response.data['results'][page_size - 1]['id'],
            tweets[page_size - 1].id,
        )

        # 2nd page
        response = self.user1_client.get(TWEET_LIST_API, {
            'user_id': self.user1.id,
            'created_at__lt': tweets[page_size - 1].created_at,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['id'], tweets[page_size].id)
        self.assertEqual(
            response.data['results'][1]['id'],
            tweets[page_size + 1].id
        )
        self.assertEqual(
            response.data['results'][page_size - 1]['id'],
            tweets[2 * page_size - 1].id,
        )

        # pull the latest page
        response = self.user1_client.get(TWEET_LIST_API, {
            'user_id': self.user1.id,
            'created_at__gt': tweets[0].created_at,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 0)

        # post a new tweet
        new_tweet = self.create_tweet(self.user1, 'a new tweet')
        response = self.user1_client.get(TWEET_LIST_API, {
            'user_id': self.user1.id,
            'created_at__gt': tweets[0].created_at,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], new_tweet.id)