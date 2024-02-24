'''
Test for recipe APIs
'''

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer
)


RECIPE_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    '''create and return a recipe detail url'''
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    '''create and return sample recipe'''
    defaults = {
        'title': 'Sample recipe title',
        'time_minutes': 22,
        'price': Decimal('5.23'),
        'description': 'Sample description',
        'link': 'http://example.com/recipe.pdf',
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)

    return recipe


def create_user(**params):
    '''create and return a new user'''
    return get_user_model().objects.create_user(**params)


class PublicRecipeTests(TestCase):
    '''Test unauthenticates api requests'''
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_reuqired(self):
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    '''Authenticated recipe test api'''

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user(email='user@example.com',
                                password='testpassword123')
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        '''Test retrieving list of recipes'''
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_list_limited_to_user(self):
        '''Test list of recipes limited ofr authenticated user'''
        other_user = create_user(
            email='other@example.com',
            password='passwordother'
        )

        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        '''test get recipe detail'''
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe_id=recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recapi(self):
        payload = {
            'title': 'Sample recipe title',
            'time_minutes': 22,
            'price': Decimal('5.23'),
            'description': 'Sample description',
            'link': 'http://example.com/recipe.pdf',
        }
        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        original_link = 'http://example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title='Sample recipe title',
            link=original_link
        )
        payload = {
            'title': 'New Recipe Title',
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        '''test full update recipe'''
        recipe = create_recipe(
            user=self.user,
            title='sample title for test recipe',
            link='http://example.com/recipe.pdf',
            description='sample description for test recipe'
        )
        payload = {
            'title': 'updated title for recipe',
            'link': 'http://example.com/new-recipe.pdf',
            'description': 'new description',
            'time_minutes': 16,
            'price': Decimal('3.69')
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        '''test changing recipe recipe user results an error'''
        new_user = create_user(email='user3@gmail.com',
                               password='user2password123')
        recipe = create_recipe(
            user=self.user,
        )
        payload = {
            'user': new_user.id,
        }
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)
        # self.assertEqual()

    def test_delete_recipe(self):
        '''test deleting recipe seccessfull'''
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_recipe_other_users_recipe_error(self):
        '''test trying to delete another users recipe gives error'''
        new_user2 = create_user(
            email='newuser2@example.com',
            password='user2password123'
        )
        recipe = create_recipe(
            user=new_user2,
        )

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())
