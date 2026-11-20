from django.test import TestCase
from django.urls import reverse

from api.filters import RESERVED_PARAMS, get_spec_fields
from goods.models import Category, Keyboard, Product


def make_keyboard(category, **kwargs):
    """A Keyboard with valid defaults for the required specifications."""
    values = {
        'manufacturer': 'Acme',
        'quantity': 1,
        'discount': 0,
        'layout': 'ANSI',
        'key_switches': 'Red',
        'backlighting': False,
        'connectivity': 'USB',
        'interface': 'USB-A',
        'dimensions': '440x130x35',
    }
    values.update(kwargs)
    return Keyboard.objects.create(category=category, **values)


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
        cls.keyboard = make_keyboard(
            cls.keyboards, name='Budget Keyboard', slug='budget-keyboard',
            manufacturer='Other', price=20, quantity=0,
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
        response = self.get_list(q='Budget')

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

        self.assertEqual(self.slugs(response), ['budget-keyboard'])

    def test_search_by_name(self):
        response = self.get_list(q='gpu')

        self.assertEqual(self.slugs(response), ['fast-gpu'])

    def test_price_filter_uses_the_discounted_price(self):
        # Test CPU costs 100 but its sell price is 90
        self.assertEqual(self.slugs(self.get_list(min_price=100)), ['fast-gpu'])
        self.assertEqual(
            self.slugs(self.get_list(max_price=90)), ['test-cpu', 'budget-keyboard']
        )

    def test_ordering(self):
        self.assertEqual(
            self.slugs(self.get_list(ordering='price')),
            ['budget-keyboard', 'test-cpu', 'fast-gpu'],
        )
        self.assertEqual(
            self.slugs(self.get_list(ordering='-price')),
            ['fast-gpu', 'test-cpu', 'budget-keyboard'],
        )
        self.assertEqual(
            self.slugs(self.get_list(ordering='name')),
            ['budget-keyboard', 'fast-gpu', 'test-cpu'],
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


class FilterTestCase(TestCase):
    """Three keyboards with different specifications, for the filter tests."""

    @classmethod
    def setUpTestData(cls):
        cls.keyboards = Category.objects.create(
            name='Keyboards', slug='keyboards', model_name='Keyboard'
        )
        # sell price 100
        make_keyboard(
            cls.keyboards, name='Keyboard One', slug='kb-one', manufacturer='Acme',
            price=100, layout='ANSI', key_switches='Red', backlighting=True,
        )
        # sell price 40 (80 with a 50% discount)
        make_keyboard(
            cls.keyboards, name='Keyboard Two', slug='kb-two', manufacturer='Acme',
            price=80, discount=50, layout='ISO', key_switches='Red', backlighting=False,
        )
        # sell price 60
        make_keyboard(
            cls.keyboards, name='Keyboard Three', slug='kb-three', manufacturer='Other',
            price=60, layout='ANSI', key_switches='Blue', backlighting=False,
        )

    def slugs(self, **params):
        response = self.client.get(reverse('api:product_list'), params)
        self.assertEqual(response.status_code, 200)
        return [product['slug'] for product in response.json()['results']]


class SpecFilterTests(FilterTestCase):
    def test_filter_by_one_specification(self):
        self.assertEqual(self.slugs(category='keyboards', layout='ANSI'), ['kb-one', 'kb-three'])

    def test_several_values_of_one_specification_are_alternatives(self):
        self.assertEqual(
            self.slugs(category='keyboards', layout=['ANSI', 'ISO']),
            ['kb-one', 'kb-two', 'kb-three'],
        )

    def test_different_specifications_must_all_match(self):
        self.assertEqual(self.slugs(category='keyboards', layout='ANSI', key_switches='Red'), ['kb-one'])

    def test_yes_no_specification(self):
        self.assertEqual(self.slugs(category='keyboards', backlighting='true'), ['kb-one'])
        self.assertEqual(self.slugs(category='keyboards', backlighting='false'), ['kb-two', 'kb-three'])

    def test_filter_by_manufacturer(self):
        self.assertEqual(self.slugs(category='keyboards', manufacturer='Other'), ['kb-three'])
        self.assertEqual(
            self.slugs(category='keyboards', manufacturer=['Acme', 'Other']),
            ['kb-one', 'kb-two', 'kb-three'],
        )

    def test_all_filters_work_together(self):
        self.assertEqual(
            self.slugs(
                category='keyboards', manufacturer='Acme', layout='ANSI',
                min_price=50, q='keyboard',
            ),
            ['kb-one'],
        )

    def test_wrong_specification_value_returns_400(self):
        url = reverse('api:product_list')

        for params in [
            {'category': 'keyboards', 'backlighting': 'maybe'},
            {'category': 'keyboards', 'weight': 'abc'},
        ]:
            with self.subTest(params=params):
                response = self.client.get(url, params)
                self.assertEqual(response.status_code, 400)
                self.assertIn(next(k for k in params if k != 'category'), response.json())

    def test_unknown_category_returns_400(self):
        response = self.client.get(reverse('api:product_list'), {'category': 'nothing'})

        self.assertEqual(response.status_code, 400)
        self.assertIn('category', response.json())

    def test_specification_without_category_is_ignored(self):
        self.assertEqual(
            self.slugs(layout='ISO'),
            ['kb-one', 'kb-two', 'kb-three'],
        )

    def test_specification_names_do_not_clash_with_other_parameters(self):
        # A new category model with a field called "page" or "q" would break its filters
        for model in Product.__subclasses__():
            with self.subTest(model=model.__name__):
                self.assertFalse(set(get_spec_fields(model)) & RESERVED_PARAMS)


class FacetsApiTests(FilterTestCase):
    def facets(self, **params):
        response = self.client.get(reverse('api:filters'), params)
        self.assertEqual(response.status_code, 200)
        return response.json()

    def options(self, facets, spec_name):
        spec = next(s for s in facets['specs'] if s['name'] == spec_name)
        return [(option['value'], option['count']) for option in spec['values']]

    def manufacturers(self, facets):
        return [(option['value'], option['count']) for option in facets['manufacturers']]

    def test_category_facets(self):
        facets = self.facets(category='keyboards')

        self.assertEqual(facets['price_range'], {'min': 40, 'max': 100})
        self.assertEqual(self.manufacturers(facets), [('Acme', 2), ('Other', 1)])
        self.assertEqual(self.options(facets, 'layout'), [('ANSI', 2), ('ISO', 1)])
        self.assertEqual(self.options(facets, 'key_switches'), [('Red', 2), ('Blue', 1)])

    def test_specifications_have_labels_and_are_sorted_by_label(self):
        specs = self.facets(category='keyboards')['specs']

        labels = [spec['label'] for spec in specs]
        self.assertEqual(labels, sorted(labels))
        self.assertEqual(
            next(s['label'] for s in specs if s['name'] == 'key_switches'), 'Key switches'
        )
        self.assertEqual(len(specs), 10)

    def test_yes_no_values_are_booleans(self):
        facets = self.facets(category='keyboards')

        self.assertEqual(self.options(facets, 'backlighting'), [(False, 2), (True, 1)])

    def test_counts_follow_the_other_filters(self):
        facets = self.facets(category='keyboards', layout='ISO')

        # Manufacturers and switches are counted inside the chosen layout
        self.assertEqual(self.manufacturers(facets), [('Acme', 1), ('Other', 0)])
        self.assertEqual(self.options(facets, 'key_switches'), [('Red', 1), ('Blue', 0)])
        # A group does not use its own selection, so the user can add another value
        self.assertEqual(self.options(facets, 'layout'), [('ANSI', 2), ('ISO', 1)])

    def test_manufacturer_selection_changes_the_specification_counts(self):
        facets = self.facets(category='keyboards', manufacturer='Other')

        self.assertEqual(self.options(facets, 'layout'), [('ANSI', 1), ('ISO', 0)])
        # ...but not the manufacturer counts themselves
        self.assertEqual(self.manufacturers(facets), [('Acme', 2), ('Other', 1)])

    def test_price_filter_changes_counts_but_not_the_price_range(self):
        facets = self.facets(category='keyboards', max_price=60)

        self.assertEqual(facets['price_range'], {'min': 40, 'max': 100})
        self.assertEqual(self.manufacturers(facets), [('Acme', 1), ('Other', 1)])

    def test_search_changes_the_price_range(self):
        facets = self.facets(category='keyboards', q='Three')

        self.assertEqual(facets['price_range'], {'min': 60, 'max': 60})

    def test_search_without_results_uses_the_whole_price_range(self):
        facets = self.facets(category='keyboards', q='no such product')

        self.assertEqual(facets['price_range'], {'min': 40, 'max': 100})

    def test_without_a_category_only_manufacturers_and_prices(self):
        facets = self.facets()

        self.assertEqual(facets['specs'], [])
        self.assertEqual(self.manufacturers(facets), [('Acme', 2), ('Other', 1)])
        self.assertEqual(facets['price_range'], {'min': 40, 'max': 100})

    def test_empty_catalog(self):
        Product.objects.all().delete()

        facets = self.facets()

        self.assertEqual(facets['price_range'], {'min': 0, 'max': 0})
        self.assertEqual(facets['manufacturers'], [])

    def test_wrong_parameters_return_400(self):
        url = reverse('api:filters')

        self.assertEqual(self.client.get(url, {'min_price': 'abc'}).status_code, 400)
        self.assertEqual(self.client.get(url, {'category': 'nothing'}).status_code, 400)
        self.assertEqual(
            self.client.get(url, {'category': 'keyboards', 'backlighting': 'x'}).status_code, 400
        )
