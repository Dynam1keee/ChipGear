from django.test import TestCase
from django.urls import reverse

from goods.models import Category


class CategoryApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Category.objects.create(name='Processors', slug='processors', model_name='CPU')
        Category.objects.create(name='Keyboards', slug='keyboards', model_name='Keyboard')

    def test_returns_all_categories(self):
        response = self.client.get(reverse('api:category_list'))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        # No pagination for categories: a plain list
        self.assertIsInstance(data, list)
        self.assertEqual([c['slug'] for c in data], ['keyboards', 'processors'])  # ordered by name
        self.assertEqual(set(data[0]), {'id', 'name', 'slug', 'image'})

    def test_response_is_json(self):
        response = self.client.get(reverse('api:category_list'))

        self.assertEqual(response['Content-Type'], 'application/json')
