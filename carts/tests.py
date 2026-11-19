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


class CartAddTests(CartTestCase):
    def test_guest_cart_gets_a_session_key(self):
        response = self.client.post(
            reverse('cart:cart_add'),
            {'product_id': self.product.id},
        )

        self.assertEqual(response.status_code, 200)
        session_key = self.client.session.session_key
        self.assertTrue(session_key)
        self.assertTrue(
            Cart.objects.filter(session_key=session_key, product=self.product, quantity=1).exists()
        )

    def test_adding_the_same_product_again_increases_quantity(self):
        url = reverse('cart:cart_add')
        self.client.post(url, {'product_id': self.product.id})
        self.client.post(url, {'product_id': self.product.id})

        cart = Cart.objects.get(session_key=self.client.session.session_key)
        self.assertEqual(cart.quantity, 2)

    def test_guest_can_change_and_remove_own_cart(self):
        self.client.post(reverse('cart:cart_add'), {'product_id': self.product.id})
        cart = Cart.objects.get(session_key=self.client.session.session_key)

        response = self.client.post(
            reverse('cart:cart_change'),
            {'cart_id': cart.id, 'quantity': 4},
        )
        self.assertEqual(response.status_code, 200)
        cart.refresh_from_db()
        self.assertEqual(cart.quantity, 4)

        response = self.client.post(reverse('cart:cart_remove'), {'cart_id': cart.id})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Cart.objects.filter(id=cart.id).exists())

    def test_cannot_add_more_than_stock(self):
        url = reverse('cart:cart_add')

        for _ in range(self.product.quantity):
            self.assertEqual(
                self.client.post(url, {'product_id': self.product.id}).status_code, 200
            )

        response = self.client.post(url, {'product_id': self.product.id})

        self.assertEqual(response.status_code, 400)
        cart = Cart.objects.get(session_key=self.client.session.session_key)
        self.assertEqual(cart.quantity, self.product.quantity)

    def test_invalid_product_id_is_rejected(self):
        url = reverse('cart:cart_add')

        self.assertEqual(self.client.post(url, {'product_id': 'abc'}).status_code, 400)
        self.assertEqual(self.client.post(url, {}).status_code, 400)
        self.assertEqual(self.client.post(url, {'product_id': 999999}).status_code, 404)

    def test_get_requests_are_not_allowed(self):
        self.assertEqual(self.client.get(reverse('cart:cart_add')).status_code, 405)


class CartChangeValidationTests(CartTestCase):
    def setUp(self):
        self.client.force_login(self.alice)
        self.url = reverse('cart:cart_change')

    def test_bad_quantity_is_rejected(self):
        for bad_value in ['abc', '', '-1', '0', '1.5']:
            with self.subTest(quantity=bad_value):
                response = self.client.post(
                    self.url,
                    {'cart_id': self.alice_cart.id, 'quantity': bad_value},
                )
                self.assertEqual(response.status_code, 400)

        self.alice_cart.refresh_from_db()
        self.assertEqual(self.alice_cart.quantity, 1)

    def test_quantity_above_stock_is_rejected(self):
        response = self.client.post(
            self.url,
            {'cart_id': self.alice_cart.id, 'quantity': self.product.quantity + 1},
        )

        self.assertEqual(response.status_code, 400)
        self.alice_cart.refresh_from_db()
        self.assertEqual(self.alice_cart.quantity, 1)

    def test_missing_or_unknown_cart_id(self):
        self.assertEqual(
            self.client.post(self.url, {'cart_id': 'abc', 'quantity': 2}).status_code, 400
        )
        self.assertEqual(
            self.client.post(self.url, {'cart_id': 999999, 'quantity': 2}).status_code, 404
        )
