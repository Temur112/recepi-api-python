'''
Testing user model
'''
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def create_user(email='testuser@example.com', password='testpass123'):
    '''create and return a new user'''
    return get_user_model().objects.create_user(email, password)


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

    def test_create_recipe(self):
        user = get_user_model().objects.create_user(
            'test@example.com',
            'testpass123',
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title='Sample title',
            time_minutes=5,
            price=Decimal('5.50'),
            description='Sample recipe decription',
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        '''test creating a tag is succesfull'''
        user = create_user()
        tag = models.Tag.objects.create(user=user, name='tag1')

        self.assertEqual(str(tag), tag.name)
