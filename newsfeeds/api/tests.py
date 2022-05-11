from newsfeeds.models import NewsFeed
from rest_framework.test import APIClient
from testing.testcases import TestCase
from utils.paginations.endless_paginations import EndlessPagination

NEWSFEEDS_URL = '/api/newsfeeds/'
POST_TWEETS_URL = '/api/tweets/'


class NewsFeedApiTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.user1 = self.create_user('testuser1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('testuser2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

    def test_list(self):
        # anonymous user cannot get newsfeed
        response = self.anonymous_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 403)

        # post method not allowed
        response = self.user1_client.post(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 405)

        # user1 post a tweet
        self.user1_client.post(POST_TWEETS_URL, {'content': 'any content'})
        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(
            response.data['results'][0]['tweet']['user']['username'],
            'testuser1'
        )
        self.assertEqual(NewsFeed.objects.count(), 1)

        # user1 follow user2 and user2 post a tweet
        self.create_friendship(self.user1, self.user2)
        self.user2_client.post(POST_TWEETS_URL, {'content': 'any content'})
        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(
            response.data['results'][0]['tweet']['user']['username'],
            'testuser2'
        )
        self.assertEqual(NewsFeed.objects.count(), 3)

    def test_endless_pagination(self):
        page_size = EndlessPagination.page_size
        newsfeeds = []
        for _ in range(page_size * 2):
            tweet = self.create_tweet(self.user2)
            newsfeed = self.create_newsfeed(self.user1, tweet)
            newsfeeds.append(newsfeed)
        newsfeeds = newsfeeds[::-1]

        # 1st page
        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['has_next_page'], True)
        self.assertEqual(response.data['results'][0]['id'], newsfeeds[0].id)
        self.assertEqual(response.data['results'][1]['id'], newsfeeds[1].id)
        self.assertEqual(
            response.data['results'][page_size - 1]['id'],
            newsfeeds[page_size - 1].id
        )

        # 2nd page
        response = self.user1_client.get(NEWSFEEDS_URL,{
            'created_at__lt': newsfeeds[page_size - 1].created_at
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(
            response.data['results'][0]['id'],
            newsfeeds[page_size].id
        )
        self.assertEqual(
            response.data['results'][1]['id'],
            newsfeeds[page_size + 1].id
        )
        self.assertEqual(
            response.data['results'][page_size - 1]['id'],
            newsfeeds[2 * page_size - 1].id
        )

        # pull the latest newsfeeds
        response = self.user1_client.get(NEWSFEEDS_URL, {
            'created_at__gt': newsfeeds[0].created_at
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)
        self.assertEqual(response.data['has_next_page'], False)

        # create a new newsfeed
        new_tweet = self.create_tweet(self.user2)
        new_newsfeed = self.create_newsfeed(self.user1, new_tweet)
        response = self.user1_client.get(NEWSFEEDS_URL, {
            'created_at__gt': newsfeeds[0].created_at
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], new_newsfeed.id)
        self.assertEqual(response.data['has_next_page'], False)

    def test_user_in_memcached(self):
        profile = self.user1.profile
        profile.nickname = 'user1_nickname'
        profile.save()

        self.create_newsfeed(self.user1, self.create_tweet(self.user2))
        self.create_newsfeed(self.user1, self.create_tweet(self.user1))
        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['results'][0]['tweet']['user']['nickname'],
            'user1_nickname'
        )
        self.assertEqual(
            response.data['results'][0]['tweet']['user']['username'],
            'testuser1'
        )
        self.assertEqual(
            response.data['results'][1]['tweet']['user']['username'],
            'testuser2'
        )

        # update username or nickname
        profile.nickname = 'user1_new_nickname'
        profile.save()
        self.user2.username = 'user2_new_username'
        self.user2.save()

        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['results'][0]['tweet']['user']['nickname'],
            'user1_new_nickname'
        )
        self.assertEqual(
            response.data['results'][0]['tweet']['user']['username'],
            'testuser1'
        )
        self.assertEqual(
            response.data['results'][1]['tweet']['user']['username'],
            'user2_new_username'
        )