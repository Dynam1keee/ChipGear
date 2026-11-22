from django.test import Client, TestCase
from django.urls import reverse

from api import discovery
from goods.models import Category, Product, RecentlyViewed
from orders.models import Order, OrderItem
from users.models import User


class DiscoveryTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name='Mice', slug='mice', model_name='Mouse')
        cls.products = [
            Product.objects.create(
                name=f'Mouse {n}', slug=f'mouse-{n}', manufacturer='Acme',
                price=10 + n, discount=0, quantity=5, category=category,
            )
            for n in range(8)
        ]
        cls.user = User.objects.create_user(username='alice', password='pass12345')

    def sell(self, product, quantity=1, order=None):
        order = order or Order.objects.create(user=self.user, phone_number='0501234567')
        OrderItem.objects.create(order=order, product=product, name=product.name, price=product.price, quantity=quantity)
        return order

    def names(self, response):
        return [item['name'] for item in response.json()]


class TopSalesTests(DiscoveryTestCase):
    def test_empty_until_there_are_enough_sold_products(self):
        for product in self.products[:discovery.TOP_SALES_MIN_PRODUCTS - 1]:
            self.sell(product)
        self.assertEqual(self.client.get(reverse('api:top_sales')).json(), [])

    def test_best_selling_first_once_there_are_enough(self):
        for product in self.products[:discovery.TOP_SALES_MIN_PRODUCTS]:
            self.sell(product)
        self.sell(self.products[3], quantity=4)
        names = self.names(self.client.get(reverse('api:top_sales')))
        self.assertEqual(names[0], 'Mouse 3')
        self.assertEqual(len(names), discovery.TOP_SALES_MIN_PRODUCTS)

    def test_products_out_of_stock_are_left_out(self):
        for product in self.products[:discovery.TOP_SALES_MIN_PRODUCTS]:
            self.sell(product)
        Product.objects.filter(pk=self.products[0].pk).update(quantity=0)
        # only five sold products are left, which is not enough
        self.assertEqual(self.client.get(reverse('api:top_sales')).json(), [])


class RelatedTests(DiscoveryTestCase):
    def test_products_from_the_same_orders(self):
        order = self.sell(self.products[0])
        self.sell(self.products[1], order=order)
        self.sell(self.products[2], order=order)
        self.sell(self.products[2])  # another order without the first product
        response = self.client.get(reverse('api:product_related', args=['mouse-0']))
        self.assertEqual(sorted(self.names(response)), ['Mouse 1', 'Mouse 2'])

    def test_no_sales_means_empty_list(self):
        response = self.client.get(reverse('api:product_related', args=['mouse-0']))
        self.assertEqual(response.json(), [])

    def test_unknown_product_is_404(self):
        self.assertEqual(self.client.get(reverse('api:product_related', args=['nope'])).status_code, 404)


class RecentlyViewedTests(DiscoveryTestCase):
    def view(self, slug, client=None):
        return (client or self.client).post(reverse('api:product_view', args=[slug]))

    def history(self, client=None, **params):
        return self.names((client or self.client).get(reverse('api:recently_viewed'), params))

    def test_guest_history_is_kept_in_the_session_newest_first(self):
        for slug in ['mouse-1', 'mouse-2', 'mouse-3', 'mouse-1']:
            self.assertEqual(self.view(slug).status_code, 204)
        self.assertEqual(self.history(), ['Mouse 1', 'Mouse 3', 'Mouse 2'])

    def test_exclude_leaves_the_current_product_out(self):
        self.view('mouse-1')
        self.view('mouse-2')
        self.assertEqual(self.history(exclude='mouse-2'), ['Mouse 1'])

    def test_each_guest_has_own_history(self):
        other = Client()
        self.view('mouse-1')
        self.assertEqual(self.history(client=other), [])

    def test_logged_in_user_history_is_kept_in_the_database(self):
        client = Client()
        client.login(username='alice', password='pass12345')
        self.view('mouse-1', client)
        self.view('mouse-2', client)
        self.view('mouse-1', client)
        self.assertEqual(RecentlyViewed.objects.filter(user=self.user).count(), 2)
        self.assertEqual(self.history(client), ['Mouse 1', 'Mouse 2'])
        # a new session of the same user sees the same history
        again = Client()
        again.login(username='alice', password='pass12345')
        self.assertEqual(self.history(again), ['Mouse 1', 'Mouse 2'])

    def test_history_is_limited(self):
        category = Category.objects.get(slug='mice')
        for n in range(discovery.HISTORY_KEEP + 5):
            Product.objects.create(
                name=f'Extra {n}', slug=f'extra-{n}', manufacturer='Acme',
                price=1, discount=0, quantity=1, category=category,
            )
            self.view(f'extra-{n}')
        self.assertEqual(len(self.client.session[discovery.SESSION_KEY]), discovery.HISTORY_KEEP)
        self.assertEqual(len(self.history()), discovery.HISTORY_LIMIT)

    def test_unknown_product_is_404(self):
        self.assertEqual(self.view('nope').status_code, 404)


class SearchSuggestionsTests(DiscoveryTestCase):
    def suggest(self, **params):
        return self.names(self.client.get(reverse('api:search_suggestions'), params))

    def test_short_text_gives_nothing(self):
        self.assertEqual(self.suggest(q='m'), [])
        self.assertEqual(self.suggest(), [])

    def test_at_most_four_products_by_name(self):
        self.assertEqual(len(self.suggest(q='mouse')), discovery.SUGGESTIONS_LIMIT)
        self.assertEqual(self.suggest(q='MOUSE 7'), ['Mouse 7'])

    def test_best_sellers_come_first(self):
        self.sell(self.products[5], quantity=3)
        self.sell(self.products[2], quantity=9)
        self.assertEqual(self.suggest(q='mouse')[:2], ['Mouse 2', 'Mouse 5'])

    def test_products_out_of_stock_are_left_out(self):
        Product.objects.filter(pk=self.products[1].pk).update(quantity=0)
        self.assertEqual(self.suggest(q='mouse 1'), [])

    def test_category_limits_the_search(self):
        other = Category.objects.create(name='Keyboards', slug='keyboards', model_name='Keyboard')
        Product.objects.create(name='Mouse pad', slug='pad', manufacturer='Acme', price=5, discount=0, quantity=1, category=other)
        self.assertEqual(self.suggest(q='mouse pad', category='keyboards'), ['Mouse pad'])
        self.assertEqual(self.suggest(q='mouse pad', category='mice'), [])
