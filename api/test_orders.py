from django.test import TestCase
from django.urls import reverse

from carts.models import Cart
from goods.models import Category, Product
from orders.models import Order
from users.models import User


class OrderApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name='Processors', slug='processors', model_name='CPU')
        # sell price 90.00, 5 in stock
        cls.cpu = Product.objects.create(
            name='Test CPU', slug='test-cpu', manufacturer='Acme',
            price=100, discount=10, quantity=5, category=category,
        )
        # sell price 20.00, 1 in stock
        cls.mouse = Product.objects.create(
            name='Test Mouse', slug='test-mouse', manufacturer='Acme',
            price=20, discount=0, quantity=1, category=category,
        )
        cls.alice = User.objects.create_user(username='alice', password='pass12345')
        cls.bob = User.objects.create_user(username='bob', password='pass12345')

    def setUp(self):
        self.url = reverse('api:orders')
        self.payload = {
            'phone_number': '0501234567',
            'requires_delivery': True,
            'delivery_address': 'Kyiv, Main st. 1',
            'payment_on_get': False,
        }

    def post(self, **changes):
        return self.client.post(self.url, {**self.payload, **changes}, content_type='application/json')

    def fill_cart(self):
        Cart.objects.create(user=self.alice, product=self.cpu, quantity=2)
        Cart.objects.create(user=self.alice, product=self.mouse, quantity=1)

    def test_guest_cannot_use_orders(self):
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.post().status_code, 403)

    def test_order_is_created_from_the_cart(self):
        self.client.force_login(self.alice)
        self.fill_cart()

        response = self.post()

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['total_price'], '200.00')  # 2 x 90 + 20
        self.assertEqual(data['status'], 'Processing')
        self.assertEqual([i['name'] for i in data['items']], ['Test CPU', 'Test Mouse'])
        self.assertEqual(data['items'][0]['total'], '180.00')

        self.assertFalse(Cart.objects.filter(user=self.alice).exists())
        self.cpu.refresh_from_db()
        self.mouse.refresh_from_db()
        self.assertEqual((self.cpu.quantity, self.mouse.quantity), (3, 0))

    def test_empty_cart_is_rejected(self):
        self.client.force_login(self.alice)

        response = self.post()

        self.assertEqual(response.status_code, 400)
        self.assertIn('non_field_errors', response.json())
        self.assertEqual(Order.objects.count(), 0)

    def test_not_enough_stock_cancels_the_whole_order(self):
        self.client.force_login(self.alice)
        self.fill_cart()
        Product.objects.filter(id=self.mouse.id).update(quantity=0)

        response = self.post()

        self.assertEqual(response.status_code, 400)
        self.assertIn('Test Mouse', response.json()['non_field_errors'][0])
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Cart.objects.filter(user=self.alice).count(), 2)
        self.cpu.refresh_from_db()
        self.assertEqual(self.cpu.quantity, 5)  # the first item was not taken either

    def test_form_validation(self):
        self.client.force_login(self.alice)
        self.fill_cart()

        for bad_phone in ['123', 'abcdefghij', '05012345678', '']:
            with self.subTest(phone=bad_phone):
                response = self.post(phone_number=bad_phone)
                self.assertEqual(response.status_code, 400)
                self.assertIn('phone_number', response.json())

        response = self.post(delivery_address='  ')
        self.assertEqual(response.status_code, 400)
        self.assertIn('delivery_address', response.json())

        self.assertEqual(Order.objects.count(), 0)

    def test_address_is_not_needed_without_delivery(self):
        self.client.force_login(self.alice)
        self.fill_cart()

        response = self.post(requires_delivery=False, delivery_address='')

        self.assertEqual(response.status_code, 201)
        self.assertIsNone(Order.objects.get().delivery_address)

    def test_user_sees_only_own_orders_newest_first(self):
        self.client.force_login(self.alice)
        for _ in range(2):
            Cart.objects.create(user=self.alice, product=self.cpu, quantity=1)
            self.assertEqual(self.post().status_code, 201)
        Order.objects.create(user=self.bob, phone_number='0501234567')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        ids = [o['id'] for o in response.json()]
        self.assertEqual(len(ids), 2)
        self.assertEqual(ids, sorted(ids, reverse=True))
        self.assertEqual(set(Order.objects.filter(user=self.alice).values_list('id', flat=True)), set(ids))

    def test_guest_cart_is_not_used(self):
        self.client.force_login(self.alice)
        Cart.objects.create(user=self.bob, product=self.cpu, quantity=1)

        self.assertEqual(self.post().status_code, 400)  # alice's cart is empty
        self.assertTrue(Cart.objects.filter(user=self.bob).exists())
