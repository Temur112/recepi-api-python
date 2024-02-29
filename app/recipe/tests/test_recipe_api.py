'''
Test for recipe APIs
'''
import tempfile
import os
from PIL import Image

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)


RECIPE_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    '''create and return image upload url'''
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


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

    def create_recipe_with_new_tag(self):
        '''test creating a new recipe with tags'''
        payload = {
            'title': 'test title',
            'time_minutes': 6.2,
            'price': Decimal('2.56'),
            'tags': [{'name': 'desert'}, {'name': 'breakfast'}]
        }
        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipe.count(), 1)
        recipe = recipe[0]
        self.assertEqual(recipe.tags.couunt(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        '''create new recipe with ecxisting tag'''
        tag_indian = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title': 'Pongal',
            'time_minutes': 60,
            'price': Decimal('5.6'),
            'tags': [{'name': 'Indian'}, {'name': 'Breakfast'}],
        }

        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        '''test creating tag when updating a recipe'''
        recipe = create_recipe(user=self.user)

        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Lunch')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assing_tag(self):
        '''Test assigning an existing tag when updating a recipe'''
        tag_breakfast = Tag.objects.create(user=self.user, name='breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {
            'tags': [{'name': 'Lunch'}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_recipe_tags(self):
        '''test clearing tags of recipe'''
        tag = Tag.objects.create(user=self.user, name='Desert')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {
            'tags': [],
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_ingredients(self):
        payload = {
            'title': 'Taco',
            'time_minutes': 45,
            'price': Decimal('9.6'),
            'ingredients': [{'name': 'Salt'}, {'name': 'Oil'}],
        }
        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                user=self.user,
                name=ingredient['name']
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredients(self):
        '''test creating recipe with existing ingredients'''
        ingredient = Ingredient.objects.create(
            user=self.user,
            name="Lemon"
        )
        payload = {
            'title': 'test recipe',
            'time_minutes': 30,
            'price': Decimal('6.8'),
            'ingredients': [
                {'name': 'Lemon'}, {'name': 'Fish souce'}
            ]
        }

        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        '''test creating a ingredient when updateing recipe'''
        recipe = create_recipe(user=self.user)

        payload = {
            'ingredients': [{'name': 'lemon'}]
        }

        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user=self.user, name='lemon')
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        '''test assigning ingredient for recipe'''
        ingredient1 = Ingredient.objects.create(user=self.user, name='Pepper')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user=self.user, name='Chili')
        payload = {
            'ingredients': [{'name': 'Chili'}],
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(ingredient1, recipe.ingredients.all())
        self.assertIn(ingredient2, recipe.ingredients.all())

    def test_clearing_recipe_ingredients(self):
        '''test for clearing ingredient of recipe'''
        ingredient = Ingredient.objects.create(
            user=self.user, name='test clear'
        )
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {
            'ingredients': [],
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)

    def test_filter_by_tags(self):
        '''test filtering recipes by tags'''
        r1 = create_recipe(user=self.user, title='anor')
        r2 = create_recipe(user=self.user, title='piyoz')
        tag1 = Tag.objects.create(user=self.user, name='meva')
        tag2 = Tag.objects.create(user=self.user, name='sabzavot')

        r1.tags.add(tag1)
        r2.tags.add(tag2)
        r3 = create_recipe(user=self.user, title='fish')

        params = {
            'tags': f'{tag1.id},{tag2.id}'
        }

        res = self.client.get(RECIPE_URL, params)
        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_by_ingredients(self):
        r1 = create_recipe(user=self.user, title='recipe 1 title')
        r2 = create_recipe(user=self.user, title='recipe 2 title')

        in1 = Ingredient.objects.create(
            user=self.user,
            name='ingredient 1 for recipe 1',
        )
        in2 = Ingredient.objects.create(
            user=self.user,
            name='ingredient 2 for recipe 2',
        )

        r1.ingredients.add(in1)
        r2.ingredients.add(in2)

        r3 = create_recipe(user=self.user, title='recepi 3')
        params = {'ingredients': f'{in1.id},{in2.id}'}

        res = self.client.get(RECIPE_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


class ImageUploadTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'testpassword123'
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        '''test uploading images'''
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {
                'image': image_file,
            }
            res = self.client.post(url, payload, fromat='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_bad_request(self):
        '''test uploading invalid image'''
        url = image_upload_url(self.recipe.id)
        payload = {
            'image': 'some text not an image',
        }

        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
