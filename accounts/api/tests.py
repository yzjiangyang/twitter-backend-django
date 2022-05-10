from accounts.models import UserProfile
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from testing.testcases import TestCase

LOGIN_URL = '/api/accounts/login/'
SIGNUP_URL = '/api/accounts/signup/'
LOGOUT_URL = '/api/accounts/logout/'
LOGIN_STATUS_URL = '/api/accounts/login_status/'
USER_PROFILE_DETAIL_URL = '/api/profiles/{}/'


class AccountApiTests(TestCase):

    def setUp(self):
        self.clear_cache
        self.user = self.create_user('testuser')
        self.user_client = APIClient()

    def test_login(self):
        # cannot use get
        response = self.user_client.get(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password'
        })
        self.assertEqual(response.status_code, 405)

        # username not exist
        response = self.user_client.post(LOGIN_URL, {
            'username': 'username not exist',
            'password': 'correct password'
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['errors']['username'][0],
            'The username does not exist.'
        )

        # password wrong
        response = self.user_client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'incorrect password'
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['message'],
            'Username and password do not match.'
        )
        # login status
        response = self.user_client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_logged_in'], False)

        # login successfully
        response = self.user_client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['success'], True)

        # login status
        response = self.user_client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_logged_in'], True)

    def test_logout(self):
        # login successfully
        self.user_client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password'
        })
        # login status
        response = self.user_client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_logged_in'], True)

        # cannot use get
        response = self.user_client.get(LOGOUT_URL)
        self.assertEqual(response.status_code, 405)

        # logout successfully
        response = self.user_client.post(LOGOUT_URL)
        self.assertEqual(response.status_code, 200)
        # login status
        response = self.user_client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_logged_in'], False)

    def test_signup(self):
        # cannot use get
        response = self.user_client.get(SIGNUP_URL, {
            'username': 'testuser',
            'email': 'testuser@gmail.com',
            'password': 'correct password'
        })
        self.assertEqual(response.status_code, 405)

        # username exist
        response = self.user_client.post(SIGNUP_URL, {
            'username': self.user.username,
            'email': 'testuser@gmail.com',
            'password': 'correct password'
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['errors']['username'][0],
            'This username has been used.'
        )

        # email exist
        response = self.user_client.post(SIGNUP_URL, {
            'username': 'newusername',
            'email': self.user.email,
            'password': 'correct password'
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['errors']['email'][0],
            'This email has been used.'
        )

        # username too short
        response = self.user_client.post(SIGNUP_URL, {
            'username': 'short',
            'email': 'short@ghmail.com',
            'password': 'correct password'
        })
        self.assertEqual(response.status_code, 400)

        # password too long
        response = self.user_client.post(SIGNUP_URL, {
            'username': 'newusername',
            'email': 'newusername@ghmail.com',
            'password': 'correct passworddddddddddddddddddddddddddddddddd'
        })
        self.assertEqual(response.status_code, 400)

        # signup successfully
        response = self.user_client.post(SIGNUP_URL, {
            'username': 'newusername',
            'email': 'newusername@ghmail.com',
            'password': 'correct password'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['success'], True)
        # test user profile
        user_id = response.data['user']['id']
        self.assertEqual(UserProfile.objects.filter(user=user_id).exists(), True)


class UserProfileAPITests(TestCase):

    def setUp(self):
        self.clear_cache
        self.user1 = self.create_user('testuser1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('testuser2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

    def test_avatar_update(self):
        # userprofile not exist
        response = self.user1_client.put(USER_PROFILE_DETAIL_URL.format(1))
        self.assertEqual(response.status_code, 404)

        # create profile
        user1_profile = self.user1.profile
        user1_profile.nickname = 'old_nickname'
        user1_profile.save()

        # other user cannot update
        url = USER_PROFILE_DETAIL_URL.format((user1_profile.id))
        response = self.user2_client.put(url, {'nickname': 'new_nickname'})
        self.assertEqual(response.status_code, 404)

        # owner update nickname
        response = self.user1_client.put(url, {'nickname': 'new_nickname'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['nickname'], 'new_nickname')
        user1_profile.refresh_from_db()
        self.assertEqual(user1_profile.nickname, 'new_nickname')

        # owner update avatar
        response = self.user1_client.put(url, {
            'avatar': SimpleUploadedFile(
                name='my-avatar.jpeg',
                content=str.encode('a test image'),
                content_type='image/jpeg'
            )
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual('my-avatar' in response.data['avatar'], True)
        user1_profile.refresh_from_db()
        self.assertNotEqual(user1_profile.avatar, None)