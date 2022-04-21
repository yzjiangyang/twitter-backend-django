from friendships.models import Friendship
from rest_framework.test import APIClient
from testing.testcases import TestCase

FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'


class FriendshipApiTests(TestCase):

    def setUp(self):
        self.user1 = self.create_user('testuser1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)
        self.followings = [
            self.create_friendship(self.user1, self.create_user(f'following{i}'))
            for i in range(2)
        ]

        self.user2 = self.create_user('testuser2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)
        self.followers = [
            self.create_friendship(self.create_user(f'follower{i}'), self.user2)
            for i in range(3)
        ]

    def test_follow(self):
        # cannot follow if not logged in
        url = FOLLOW_URL.format(self.user2.id)
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)

        # cannot use get
        response = self.user1_client.get(url)
        self.assertEqual(response.status_code, 405)

        # user not exist
        response = self.user1_client.post(FOLLOW_URL.format(0))
        self.assertEqual(response.status_code, 404)

        # cannot follow yourself
        response = self.user2_client.post(url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['errors']['message'][0],
            'You cannot follow yourself.'
        )

        # follow successfully
        response = self.user1_client.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['username'], 'testuser2')

        # follow again
        response = self.user1_client.post(url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['errors']['message'][0],
            'You have already followed this user.'
        )

        # new follow add 1 more record
        count = Friendship.objects.count()
        response = self.user2_client.post(FOLLOW_URL.format(self.user1.id))
        self.assertEqual(response.status_code, 201)
        new_count = Friendship.objects.count()
        self.assertEqual(new_count, count + 1)

    def test_unfollow(self):
        # cannot follow if not logged in
        url = UNFOLLOW_URL.format(self.user2.id)
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)

        # cannot unfollow yourself
        response = self.user2_client.post(url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['message'],
            'You cannot unfollow yourself.'
        )

        # create friendship
        self.create_friendship(self.user1, self.user2)

        # cannot user get
        response = self.user1_client.get(url)
        self.assertEqual(response.status_code, 405)

        # user not exist
        response = self.user1_client.post(FOLLOW_URL.format(0))
        self.assertEqual(response.status_code, 404)

        # unfollow successfully
        count = Friendship.objects.count()
        response = self.user1_client.post(url)
        new_count = Friendship.objects.count()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(new_count, count - 1)

        # unfollow again
        count = Friendship.objects.count()
        response = self.user1_client.post(url)
        new_count = Friendship.objects.count()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(new_count, count)

    def test_followings(self):
        url = FOLLOWINGS_URL.format(self.user1.id)

        # cannot use post
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)

        # get is ok
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followings']), 2)
        self.assertEqual(
            response.data['followings'][0]['user']['id'],
            self.followings[1].to_user_id
        )
        self.assertEqual(
            response.data['followings'][1]['user']['id'],
            self.followings[0].to_user_id
        )

    def test_followers(self):
        url = FOLLOWERS_URL.format(self.user2.id)

        # cannot use post
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)

        # get is ok
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followers']), 3)
        self.assertEqual(
            response.data['followers'][0]['user']['id'],
            self.followers[2].from_user_id
        )
        self.assertEqual(
            response.data['followers'][2]['user']['id'],
            self.followers[0].from_user_id
        )
