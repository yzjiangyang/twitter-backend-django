from testing.testcases import TestCase


class commentModelTests(TestCase):

    def test_comment_model(self):
        user = self.create_user('testuser')
        tweet = self.create_tweet(user)
        content = 'any content'
        comment = self.create_comment(user, tweet, content)
        self.assertEqual(
            comment.__str__(),
            '{} - {} says {} at tweet {}'.format(
                comment.created_at,
                user,
                content,
                tweet
            )
        )