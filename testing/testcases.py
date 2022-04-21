from comments.models import Comment
from django.contrib.auth.models import User
from django.test import TestCase as DjangoTestCase
from friendships.models import Friendship
from rest_framework.test import APIClient
from tweets.models import Tweet


class TestCase(DjangoTestCase):

    # under same test class, only create one anonymous_user
    @property
    def anonymous_client(self):
        if hasattr(self, '_anonymous_user'):
            return self._anonymous_user
        self._anonymous_user = APIClient()
        return self._anonymous_user

    def create_user(self, username, email=None, password=None):
        if email is None:
            email = '{}@gmail.com'.format(username)
            password = 'correct password'

        return User.objects.create_user(username, email, password)

    def create_tweet(self, user, content=None):
        if content is None:
            content = 'any content'

        return Tweet.objects.create(user=user, content=content)

    def create_friendship(self, from_user, to_user):
        return Friendship.objects.create(from_user=from_user, to_user=to_user)

    def create_comment(self, user, tweet, content=None):
        if content == None:
            content = "any content"
        return Comment.objects.create(user=user, tweet=tweet, content=content)