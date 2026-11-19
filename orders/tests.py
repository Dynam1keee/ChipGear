from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from carts.models import Cart
from goods.models import Category, Product
from orders.models import Order, OrderItem
from users.models import User


class CreateOrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='alice', password='pass12345')
        category = Category.objects.create(
            name='Processors', slug='processors', model_name='CPU'
        )
        cls.product = Product.objects.create(
            name='Test CPU',
            slug='test-cpu',
            manufacturer='Acme',
            price=100,
            quantity=5,
            category=category,
        )

    def setUp(self):
        self.client.force_login(self.user)
        self.url = reverse('orders:create_order')
        self.order_data = {
            'first_name': 'Alice',
            'last_name': 'Smith',
            'phone_number': '0123456789',
            'requires_delivery': '0',
            'delivery_address': '',
            'payment_on_get': '0',
        }

    def messages(self, response):
        return [str(m) for m in get_messages(response.wsgi_request)]

    def test_order_is_created_and_stock_is_reduced(self):
        Cart.objects.create(user=self.user, product=self.product, quantity=2)

        response = self.client.post(self.url, self.order_data)

        self.assertRedirects(
            response, reverse('user:profile'), fetch_redirect_response=False
        )
        order = Order.objects.get()
        item = OrderItem.objects.get(order=order)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.name, 'Test CPU')
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 3)
        self.assertFalse(Cart.objects.filter(user=self.user).exists())

    def test_empty_cart_does_not_create_an_order(self):
        response = self.client.post(self.url, self.order_data)

        self.assertRedirects(
            response, reverse('user:users_cart'), fetch_redirect_response=False
        )
        self.assertIn('Your cart is empty', self.messages(response))
        self.assertFalse(Order.objects.exists())

    def test_not_enough_stock_rolls_everything_back(self):
        Cart.objects.create(user=self.user, product=self.product, quantity=9)

        response = self.client.post(self.url, self.order_data)

        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        self.assertTrue(
            any('Insufficient product quantity' in m for m in self.messages(response))
        )
        self.assertFalse(Order.objects.exists())
        self.assertFalse(OrderItem.objects.exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 5)
        self.assertTrue(Cart.objects.filter(user=self.user).exists())

    def test_invalid_phone_number_shows_the_form_again(self):
        Cart.objects.create(user=self.user, product=self.product, quantity=1)
        self.order_data['phone_number'] = '12ab'

        response = self.client.post(self.url, self.order_data)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Order.objects.exists())
