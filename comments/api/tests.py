from comments.models import Comment
from rest_framework.test import APIClient
from testing.testcases import TestCase

COMMENT_UTL = '/api/comments/'
COMMENT_DETAIL_URL = '/api/comments/{}/'


class CommentApiTest(TestCase):

    def setUp(self):
        self.user1 = self.create_user('testuser1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)
        self.tweet = self.create_tweet(self.user1)

        self.user2 = self.create_user('testuser2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

    def test_list(self):
        # missing parameter
        response = self.anonymous_client.get(COMMENT_UTL)
        self.assertEqual(response.status_code, 400)

        # with tweet_id
        response = self.anonymous_client.get(
            COMMENT_UTL,
            {'tweet_id': self.tweet.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['comments']), 0)

        # create 2 comments
        self.create_comment(self.user1, self.tweet)
        self.create_comment(self.user2, self.tweet)

        # comments order by time
        another_tweet = self.create_tweet(self.user1)
        self.create_comment(self.user2, another_tweet)

        response = self.anonymous_client.get(
            COMMENT_UTL,
            {'tweet_id': self.tweet.id}
        )
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

    def test_update(self):
        # create comment
        comment = self.create_comment(self.user1, self.tweet)

        # anonymous user cannot update
        url = COMMENT_DETAIL_URL.format(comment.id)
        response = self.anonymous_client.put(url)
        self.assertEqual(response.status_code, 403)

        # other user cannot update
        response = self.user2_client.put(url)
        self.assertEqual(response.status_code, 403)

        # can only update content
        before_updated_at = comment.updated_at
        another_tweet = self.create_tweet(self.user1)
        response = self.user1_client.put(url, {
            'user_id': self.user2.id,
            'tweet_id': another_tweet.id,
            'content': 'new content'
        })
        # refresh comment
        comment.refresh_from_db()
        after_updated_at = comment.updated_at
        self.assertEqual(response.status_code, 200)
        self.assertEqual(comment.content, 'new content')
        self.assertEqual(comment.user_id, self.user1.id)
        self.assertEqual(comment.tweet_id, self.tweet.id)
        self.assertNotEqual(before_updated_at, after_updated_at)

    def test_destroy(self):
        # create comment
        comment = self.create_comment(self.user1, self.tweet)

        # anonymous user cannot delete
        url = COMMENT_DETAIL_URL.format(comment.id)
        response = self.anonymous_client.delete(url)
        self.assertEqual(response.status_code, 403)

        # other user cannot update
        response = self.user2_client.delete(url)
        self.assertEqual(response.status_code, 403)

        # delete successfully
        before_delete_count = Comment.objects.count()
        response = self.user1_client.delete(url)
        after_delete_count = Comment.objects.count()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(before_delete_count - 1, after_delete_count)