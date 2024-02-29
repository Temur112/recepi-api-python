'''Test for ingredient api'''
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


def detail_url(ingredient_id):
    '''create and return url for specific ingredient'''
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_user(email='user@example.com', password='testpassword123'):
    '''creating and returning user'''
    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientsTest(TestCase):
    '''Test unauthenticated Api requests'''

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        '''Test auth is required to retrieve ingredeints'''
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsTest(TestCase):
    '''authenticated test api'''

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieving_ingredients(self):
        '''Test retrieving a list of ingredients'''
        Ingredient.objects.create(
            user=self.user,
            name="Kale"
        )

        Ingredient.objects.create(
            user=self.user,
            name="Kale2"
        )
        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        '''Test list of ingredients authenticated user'''
        user2 = create_user(email='user2@example.com')
        Ingredient.objects.create(user=user2, name='Salt')
        ingredeint = Ingredient.objects.create(user=self.user, name='Pepper')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredeint.name)
        self.assertEqual(res.data[0]['id'], ingredeint.id)

    def test_update_ingredient(self):
        '''test updating an ingredient'''
        ingredient = Ingredient.objects.create(
            user=self.user, name='test name'
        )

        payload = {
            'name': 'updated name',
        }
        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):
        '''test deleting ingredient'''
        ingredient = Ingredient.objects.create(user=self.user, name='testname')

        url = detail_url(ingredient.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())

    def test_filter_ingredients_assigned_to_recipe(self):
        '''Test listing ingredients to those assigned to recipe'''
        in1 = Ingredient.objects.create(
            user=self.user,
            name='Apple'
        )
        in2 = Ingredient.objects.create(
            user=self.user,
            name='Turkey'
        )

        recipe = Recipe.objects.create(
            title='Apple Crumble',
            time_minutes=5,
            price=Decimal('5.6'),
            user=self.user,
        )

        recipe.ingredients.add(in1)
        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        s1 = IngredientSerializer(in1)
        s2 = IngredientSerializer(in2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_ingredients_unique(self):
        '''Test filtered ingredients return a unique list'''
        ing = Ingredient.objects.create(
            user=self.user,
            name="Eggs"
        )
        Ingredient.objects.create(
            user=self.user,
            name=''
        )

        recipe1 = Recipe.objects.create(
            title='Egg benedict',
            time_minutes=60,
            price=Decimal('9.3'),
            user=self.user
        )

        recipe2 = Recipe.objects.create(
            title='Herb egg',
            time_minutes=35,
            price=Decimal('4.2'),
            user=self.user
        )

        recipe1.ingredients.add(ing)
        recipe2.ingredients.add(ing)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
