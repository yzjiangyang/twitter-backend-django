from django.conf import settings
from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedService
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

    def test_tweet_in_memcached(self):
        tweet = self.create_tweet(self.user1, 'old content')
        self.create_newsfeed(self.user2, tweet)
        response = self.user2_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['results'][0]['tweet']['user']['username'],
            'testuser1'
        )
        self.assertEqual(
            response.data['results'][0]['tweet']['content'],
            'old content'
        )

        # update username
        self.user1.username = 'newtestuser1'
        self.user1.save()
        response = self.user2_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['results'][0]['tweet']['user']['username'],
            'newtestuser1'
        )

        # update content
        tweet.content = 'new content'
        tweet.save()
        response = self.user2_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['results'][0]['tweet']['content'],
            'new content'
        )

    def _paginate_to_get_all_newsfeeds(self, client):
        response = client.get(NEWSFEEDS_URL)
        results = response.data['results']
        while response.data['has_next_page']:
            created_at__lt = response.data['results'][-1]['created_at']
            response = client.get(NEWSFEEDS_URL, {'created_at__lt': created_at__lt})
            results.extend(response.data['results'])

        return results

    def test_cached_limit_size_in_redis(self):
        list_limit = settings.REDIS_LIST_LENGTH_LIMIT
        page_size = EndlessPagination.page_size
        users = [self.create_user('user{}'.format(i)) for i in range(5)]
        newsfeeds = []
        for i in range(list_limit + page_size):
            tweet = self.create_tweet(users[i % 5])
            newsfeed = self.create_newsfeed(self.user1, tweet)
            newsfeeds.append(newsfeed)
        newsfeeds = newsfeeds[::-1]

        # only cache limited objects
        cached_newsfeeds = NewsFeedService.get_cached_newsfeeds_from_redis(self.user1.id)
        self.assertEqual(len(cached_newsfeeds), list_limit)
        queryset = NewsFeed.objects.filter(user_id=self.user1.id)
        self.assertEqual(len(queryset), list_limit + page_size)

        # test through api
        results = self._paginate_to_get_all_newsfeeds(self.user1_client)
        self.assertEqual(len(results), list_limit + page_size)
        for i in range(list_limit + page_size):
            self.assertEqual(newsfeeds[i].id, results[i]['id'])

        # a new tweet is created
        new_tweet = self.create_tweet(self.user2)
        new_newsfeed = self.create_newsfeed(self.user1, new_tweet)
        newsfeeds.insert(0, new_newsfeed)

        def _test_newsfeeds_after_new_feed_pushed():
            results = self._paginate_to_get_all_newsfeeds(self.user1_client)
            self.assertEqual(len(results), list_limit + page_size + 1)
            for i in range(list_limit + page_size + 1):
                self.assertEqual(newsfeeds[i].id, results[i]['id'])
        _test_newsfeeds_after_new_feed_pushed()

        # cache expired
        self.clear_cache()
        _test_newsfeeds_after_new_feed_pushed()