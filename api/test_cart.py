import json

from django.test import Client, TestCase
from django.urls import reverse

from carts.models import Cart
from goods.models import Category, Product
from users.models import User


class CartApiTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name='Processors', slug='processors', model_name='CPU')
        # sell price 90.00, 5 in stock
        cls.cpu = Product.objects.create(
            name='Test CPU', slug='test-cpu', manufacturer='Acme',
            price=100, discount=10, quantity=5, category=category,
        )
        # sell price 20.00, only 1 in stock
        cls.mouse = Product.objects.create(
            name='Test Mouse', slug='test-mouse', manufacturer='Acme',
            price=20, discount=0, quantity=1, category=category,
        )
        cls.alice = User.objects.create_user(username='alice', password='pass12345')
        cls.bob = User.objects.create_user(username='bob', password='pass12345')

    # helpers: every call returns the response
    def get_cart(self, client=None):
        return (client or self.client).get(reverse('api:cart'))

    def add(self, product, client=None):
        return (client or self.client).post(
            reverse('api:cart_items'), {'product_id': product.id}
        )

    def change(self, item_id, quantity, client=None):
        return (client or self.client).patch(
            reverse('api:cart_item', args=[item_id]),
            data=json.dumps({'quantity': quantity}),
            content_type='application/json',
        )

    def remove(self, item_id, client=None):
        return (client or self.client).delete(reverse('api:cart_item', args=[item_id]))


class CartReadAndAddTests(CartApiTestCase):
    def test_new_guest_has_an_empty_cart(self):
        response = self.get_cart()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {'items': [], 'total_quantity': 0, 'total_price': '0.00'}
        )
        self.assertTrue(self.client.session.session_key)

    def test_guest_adds_a_product(self):
        response = self.add(self.cpu)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['items']), 1)
        item = data['items'][0]
        self.assertEqual(item['quantity'], 1)
        self.assertEqual(item['total'], '90.00')
        self.assertEqual(item['product']['slug'], 'test-cpu')
        self.assertEqual(item['product']['sell_price'], '90.00')
        self.assertEqual(item['product']['category'], 'processors')
        self.assertNotIn('description', item['product'])
        self.assertEqual(data['total_quantity'], 1)
        self.assertEqual(data['total_price'], '90.00')

    def test_guest_cart_is_saved_with_the_session_key(self):
        self.add(self.cpu)

        cart = Cart.objects.get()
        self.assertEqual(cart.session_key, self.client.session.session_key)
        self.assertIsNone(cart.user)

    def test_adding_the_same_product_again_increases_quantity(self):
        self.add(self.cpu)
        data = self.add(self.cpu).json()

        self.assertEqual(len(data['items']), 1)
        self.assertEqual(data['items'][0]['quantity'], 2)
        self.assertEqual(data['items'][0]['total'], '180.00')

    def test_totals_of_several_items(self):
        self.add(self.cpu)
        self.add(self.cpu)
        data = self.add(self.mouse).json()

        self.assertEqual(data['total_quantity'], 3)
        self.assertEqual(data['total_price'], '200.00')  # 2 x 90 + 20

    def test_logged_in_user_cart_belongs_to_the_user(self):
        self.client.force_login(self.alice)

        self.add(self.cpu)

        cart = Cart.objects.get()
        self.assertEqual(cart.user, self.alice)
        self.assertIsNone(cart.session_key)

    def test_cannot_add_more_than_the_stock(self):
        self.add(self.mouse)

        response = self.add(self.mouse)  # only 1 in stock

        self.assertEqual(response.status_code, 400)
        self.assertIn('product_id', response.json())
        self.assertEqual(Cart.objects.get().quantity, 1)

    def test_bad_product_id(self):
        url = reverse('api:cart_items')

        self.assertEqual(self.client.post(url, {'product_id': 'abc'}).status_code, 400)
        self.assertEqual(self.client.post(url, {'product_id': 0}).status_code, 400)
        self.assertEqual(self.client.post(url, {}).status_code, 400)
        self.assertEqual(self.client.post(url, {'product_id': 999999}).status_code, 404)
        self.assertFalse(Cart.objects.exists())


class CartChangeAndRemoveTests(CartApiTestCase):
    def setUp(self):
        self.add(self.cpu)
        self.item_id = Cart.objects.get().id

    def test_set_quantity(self):
        response = self.change(self.item_id, 3)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['items'][0]['quantity'], 3)
        self.assertEqual(data['total_price'], '270.00')

    def test_quantity_above_stock_is_rejected(self):
        response = self.change(self.item_id, 6)  # 5 in stock

        self.assertEqual(response.status_code, 400)
        self.assertIn('quantity', response.json())
        self.assertEqual(Cart.objects.get().quantity, 1)

    def test_bad_quantity_is_rejected(self):
        for bad in [0, -1, 'abc', None, 1.5, 100000]:
            with self.subTest(quantity=bad):
                self.assertEqual(self.change(self.item_id, bad).status_code, 400)

        self.assertEqual(Cart.objects.get().quantity, 1)

    def test_remove_item(self):
        response = self.remove(self.item_id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['items'], [])
        self.assertFalse(Cart.objects.exists())

    def test_unknown_item(self):
        self.assertEqual(self.change(999999, 2).status_code, 404)
        self.assertEqual(self.remove(999999).status_code, 404)


class CartOwnershipTests(CartApiTestCase):
    def test_guests_have_separate_carts(self):
        other_guest = Client()

        self.add(self.cpu)
        self.add(self.mouse, client=other_guest)

        mine = self.get_cart().json()['items']
        theirs = self.get_cart(client=other_guest).json()['items']
        self.assertEqual([i['product']['slug'] for i in mine], ['test-cpu'])
        self.assertEqual([i['product']['slug'] for i in theirs], ['test-mouse'])

    def test_user_cannot_change_or_remove_another_users_item(self):
        bob_item = Cart.objects.create(user=self.bob, product=self.cpu, quantity=1)
        self.client.force_login(self.alice)

        self.assertEqual(self.change(bob_item.id, 3).status_code, 404)
        self.assertEqual(self.remove(bob_item.id).status_code, 404)

        bob_item.refresh_from_db()
        self.assertEqual(bob_item.quantity, 1)

    def test_guest_cannot_change_or_remove_a_users_item(self):
        bob_item = Cart.objects.create(user=self.bob, product=self.cpu, quantity=1)

        self.assertEqual(self.change(bob_item.id, 3).status_code, 404)
        self.assertEqual(self.remove(bob_item.id).status_code, 404)
        self.assertTrue(Cart.objects.filter(id=bob_item.id).exists())

    def test_user_does_not_see_other_carts(self):
        Cart.objects.create(user=self.bob, product=self.cpu, quantity=2)
        self.client.force_login(self.alice)

        self.assertEqual(self.get_cart().json()['items'], [])
