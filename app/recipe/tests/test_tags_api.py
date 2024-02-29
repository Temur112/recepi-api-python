'''test for tags api'''
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer


TAGS_URL = reverse('recipe:tag-list')


def detail_url(tag_id):
    '''creaete and return tag detail url'''
    return reverse('recipe:tag-detail', args=[tag_id])


def create_user(email='user@example.com', password='testuserpass123'):
    '''create and return a user'''
    return get_user_model().objects.create_user(email, password)


class PublicTagsApiTest(TestCase):
    '''TEst unauthorized API requests'''

    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        '''test auth is required for retrieving tags'''

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTest(TestCase):
    '''test authenticated requests '''

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Desert')

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')

        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def tags_limited_to_user(self):
        '''test limited tags for user'''
        user2 = create_user(email='user2@example.com')
        Tag.objects.create(user=user2, name='Fruity')

        tag = Tag.objects.create(user=self.user, name='tagfromuser2')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_update_tag(self):
        '''test updating a tag'''
        tag = Tag.objects.create(user=self.user, name='after dinner')

        payload = {
            'name': 'Dessert',
        }

        url = detail_url(tag.id)

        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        '''test delete tag api'''
        tag = Tag.objects.create(user=self.user, name='choco')

        url = detail_url(tag.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        tags = Tag.objects.filter(user=self.user)

        self.assertFalse(tags.exists())

    def test_filter_tags_assigned_to_recipe(self):
        '''Test listing tags to those assigned to recipes'''
        tag1 = Tag.objects.create(user=self.user, name="Breakfast")
        tag2 = Tag.objects.create(user=self.user, name="Lunch")

        recipe = Recipe.objects.create(
            title="Green Eggs on Toast",
            time_minutes=15.6,
            price=Decimal('10.3'),
            user=self.user,
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def filtered_tags_unique(self):
        '''test filtered tags reutrns unique list'''
        tag = Tag.objects.create(user=self.user, name="Dinner")
        Tag.objects.create(user=self.user, name='Lunch')
        recipe1 = Recipe.objects.create(
            title='Pancakes',
            time_minutes=5,
            price=Decimal('3.2'),
            user=self.user,
        )

        recipe2 = Recipe.objects.create(
            title='Test recipe2',
            time_minutes=3,
            price=Decimal('2.1'),
            user=self.user
        )

        recipe1.tags.add(tag)
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
