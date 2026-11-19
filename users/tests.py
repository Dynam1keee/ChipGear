from django.test import TestCase
from django.urls import reverse

from carts.models import Cart
from goods.models import Category, Product
from users.models import User


class LoginRedirectTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='alice', password='pass12345')

    def login(self, next_url=None):
        data = {'username': 'alice', 'password': 'pass12345'}
        if next_url is not None:
            data['next'] = next_url
        return self.client.post(reverse('user:login'), data)

    def test_login_redirects_to_local_next_page(self):
        response = self.login(reverse('user:profile'))

        self.assertRedirects(
            response, reverse('user:profile'), fetch_redirect_response=False
        )

    def test_login_ignores_external_next_page(self):
        for external in ['https://evil.example/', '//evil.example/', 'http://evil.example']:
            with self.subTest(next=external):
                response = self.login(external)

                self.assertRedirects(
                    response, reverse('main:index'), fetch_redirect_response=False
                )
                self.client.logout()

    def test_login_without_next_goes_to_home_page(self):
        response = self.login()

        self.assertRedirects(
            response, reverse('main:index'), fetch_redirect_response=False
        )


class LoginCartTests(TestCase):
    """A guest cart must follow the user after login."""

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

    def test_guest_cart_moves_to_user_after_login(self):
        self.client.post(reverse('cart:cart_add'), {'product_id': self.product.id})
        guest_cart = Cart.objects.get(product=self.product)
        self.assertIsNone(guest_cart.user)

        self.client.post(
            reverse('user:login'),
            {'username': 'alice', 'password': 'pass12345'},
        )

        guest_cart.refresh_from_db()
        self.assertEqual(guest_cart.user, self.user)
