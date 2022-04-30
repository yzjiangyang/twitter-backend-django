from accounts.models import UserProfile
from testing.testcases import TestCase


class UserProfileTests(TestCase):

    def test_userprofile(self):
        user1 = self.create_user('testuser1')
        self.assertEqual(UserProfile.objects.count(), 0)
        profile = user1.profile
        self.assertEqual(isinstance(profile, UserProfile), True)
        self.assertEqual(UserProfile.objects.count(), 1)