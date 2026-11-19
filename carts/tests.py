from django.test import TestCase
from django.urls import reverse

from carts.models import Cart
from goods.models import Category, Product
from users.models import User


class CartTestCase(TestCase):
    """Shared data for the cart tests."""

    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            name='Processors',
            slug='processors',
            model_name='CPU',
        )
        cls.product = Product.objects.create(
            name='Test CPU',
            slug='test-cpu',
            manufacturer='Acme',
            price=100,
            quantity=5,
            category=cls.category,
        )
        cls.alice = User.objects.create_user(username='alice', password='pass12345')
        cls.bob = User.objects.create_user(username='bob', password='pass12345')

        cls.alice_cart = Cart.objects.create(user=cls.alice, product=cls.product, quantity=1)
        cls.bob_cart = Cart.objects.create(user=cls.bob, product=cls.product, quantity=1)


class CartOwnershipTests(CartTestCase):
    """A user must only be able to change or remove their own cart."""

    def test_user_can_change_own_cart(self):
        self.client.force_login(self.alice)

        response = self.client.post(
            reverse('cart:cart_change'),
            {'cart_id': self.alice_cart.id, 'quantity': 3},
        )

        self.assertEqual(response.status_code, 200)
        self.alice_cart.refresh_from_db()
        self.assertEqual(self.alice_cart.quantity, 3)

    def test_user_cannot_change_other_users_cart(self):
        self.client.force_login(self.alice)

        response = self.client.post(
            reverse('cart:cart_change'),
            {'cart_id': self.bob_cart.id, 'quantity': 3},
        )

        self.assertEqual(response.status_code, 404)
        self.bob_cart.refresh_from_db()
        self.assertEqual(self.bob_cart.quantity, 1)

    def test_user_can_remove_own_cart(self):
        self.client.force_login(self.alice)

        response = self.client.post(
            reverse('cart:cart_remove'),
            {'cart_id': self.alice_cart.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Cart.objects.filter(id=self.alice_cart.id).exists())

    def test_user_cannot_remove_other_users_cart(self):
        self.client.force_login(self.alice)

        response = self.client.post(
            reverse('cart:cart_remove'),
            {'cart_id': self.bob_cart.id},
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Cart.objects.filter(id=self.bob_cart.id).exists())

    def test_guest_cannot_touch_a_users_cart(self):
        response = self.client.post(
            reverse('cart:cart_change'),
            {'cart_id': self.bob_cart.id, 'quantity': 3},
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.post(
            reverse('cart:cart_remove'),
            {'cart_id': self.bob_cart.id},
        )
        self.assertEqual(response.status_code, 404)

        self.bob_cart.refresh_from_db()
        self.assertEqual(self.bob_cart.quantity, 1)
