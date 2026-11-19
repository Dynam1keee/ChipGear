from django.test import TestCase
from django.urls import reverse

from goods.models import Category, Keyboard, Product


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


class ProductApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.processors = Category.objects.create(
            name='Processors', slug='processors', model_name='CPU'
        )
        cls.keyboards = Category.objects.create(
            name='Keyboards', slug='keyboards', model_name='Keyboard'
        )
        # sell price 90.00
        cls.cpu = Product.objects.create(
            name='Test CPU', slug='test-cpu', manufacturer='Acme',
            price=100, discount=10, quantity=5, category=cls.processors,
        )
        # sell price 150.00
        cls.gpu = Product.objects.create(
            name='Fast GPU', slug='fast-gpu', manufacturer='Acme',
            price=300, discount=50, quantity=2, category=cls.processors,
        )
        # sell price 20.00, out of stock
        cls.mouse = Product.objects.create(
            name='Budget Mouse', slug='budget-mouse', manufacturer='Other',
            price=20, discount=0, quantity=0, category=cls.keyboards,
        )

    def get_list(self, **params):
        return self.client.get(reverse('api:product_list'), params)

    def slugs(self, response):
        return [p['slug'] for p in response.json()['results']]

    # --- list ---

    def test_list_is_paginated(self):
        response = self.get_list()

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(set(data), {'count', 'next', 'previous', 'results'})
        self.assertEqual(data['count'], 3)

    def test_list_item_fields(self):
        response = self.get_list(q='Test CPU')

        item = response.json()['results'][0]
        self.assertEqual(item['slug'], 'test-cpu')
        self.assertEqual(item['category'], 'processors')
        self.assertEqual(item['price'], '100.00')
        self.assertEqual(item['sell_price'], '90.00')
        self.assertIs(item['in_stock'], True)

    def test_out_of_stock_flag(self):
        response = self.get_list(q='Mouse')

        self.assertIs(response.json()['results'][0]['in_stock'], False)

    def test_second_page(self):
        for number in range(25):
            Product.objects.create(
                name=f'Extra {number}', slug=f'extra-{number}', manufacturer='Acme',
                price=10, quantity=1, category=self.processors,
            )

        first = self.get_list().json()
        second = self.get_list(page=2).json()

        self.assertEqual(first['count'], 28)
        self.assertEqual(len(first['results']), 20)
        self.assertIsNotNone(first['next'])
        self.assertEqual(len(second['results']), 8)

    # --- filters ---

    def test_filter_by_category(self):
        response = self.get_list(category='keyboards')

        self.assertEqual(self.slugs(response), ['budget-mouse'])

    def test_search_by_name(self):
        response = self.get_list(q='gpu')

        self.assertEqual(self.slugs(response), ['fast-gpu'])

    def test_price_filter_uses_the_discounted_price(self):
        # Test CPU costs 100 but its sell price is 90
        self.assertEqual(self.slugs(self.get_list(min_price=100)), ['fast-gpu'])
        self.assertEqual(
            self.slugs(self.get_list(max_price=90)), ['test-cpu', 'budget-mouse']
        )

    def test_ordering(self):
        self.assertEqual(
            self.slugs(self.get_list(ordering='price')),
            ['budget-mouse', 'test-cpu', 'fast-gpu'],
        )
        self.assertEqual(
            self.slugs(self.get_list(ordering='-price')),
            ['fast-gpu', 'test-cpu', 'budget-mouse'],
        )
        self.assertEqual(
            self.slugs(self.get_list(ordering='name')),
            ['budget-mouse', 'fast-gpu', 'test-cpu'],
        )

    def test_bad_query_parameters_return_400(self):
        for params in [{'min_price': 'abc'}, {'ordering': 'size'}, {'max_price': '-5'}]:
            with self.subTest(params=params):
                self.assertEqual(self.get_list(**params).status_code, 400)

    # --- detail ---

    def test_detail_of_a_plain_product_has_empty_specs(self):
        response = self.client.get(reverse('api:product_detail', args=['test-cpu']))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['name'], 'Test CPU')
        self.assertEqual(data['specs'], {})

    def test_detail_contains_category_specs(self):
        Keyboard.objects.create(
            name='Test Keyboard', slug='test-keyboard', manufacturer='Acme',
            price=50, quantity=3, category=self.keyboards,
            layout='ANSI', key_switches='Red', connectivity='USB',
            interface='USB-A', dimensions='440x130x35',
        )

        response = self.client.get(reverse('api:product_detail', args=['test-keyboard']))

        self.assertEqual(response.status_code, 200)
        specs = response.json()['specs']
        self.assertEqual(specs['Layout'], 'ANSI')
        self.assertEqual(specs['Key switches'], 'Red')
        self.assertIs(specs['Backlighting'], False)

    def test_unknown_product_returns_404(self):
        response = self.client.get(reverse('api:product_detail', args=['no-such-product']))

        self.assertEqual(response.status_code, 404)
