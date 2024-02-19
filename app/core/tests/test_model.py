'''
Testing user model
'''
from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTest(TestCase):
    '''Test model'''

    def test_create_user_with_email_seccessfull(self):
        email = 'test@example.com'
        password = 'testpass123'
        User = get_user_model()
        user = User.objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
            ['test4@example.com', 'test4@example.com'],
        ]

        for example, expected in sample_emails:
            user = get_user_model().objects.create_user(example, "sample")
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        '''Test creating a user without email rasies an error'''

        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'testName')

    def test_create_superuser(self):
        '''test creating superuser'''
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'testUserName',
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
