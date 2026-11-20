import json

from django.test import Client, TestCase
from django.urls import reverse

from carts.models import Cart
from goods.models import Category, Product
from users.models import User

STRONG_PASSWORD = 'Xk9!mQ2#rTz'


class AuthApiTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name='Processors', slug='processors', model_name='CPU')
        cls.cpu = Product.objects.create(
            name='Test CPU', slug='test-cpu', manufacturer='Acme',
            price=100, discount=10, quantity=5, category=category,
        )
        cls.mouse = Product.objects.create(
            name='Test Mouse', slug='test-mouse', manufacturer='Acme',
            price=20, discount=0, quantity=3, category=category,
        )
        cls.alice = User.objects.create_user(
            username='alice', password='pass12345', first_name='Alice', email='alice@example.com'
        )

    def post_json(self, name, data, client=None, **extra):
        return (client or self.client).post(
            reverse(name), data=json.dumps(data), content_type='application/json', **extra
        )

    def login(self, client=None, password='pass12345'):
        return self.post_json('api:login', {'username': 'alice', 'password': password}, client)

    def me(self, client=None):
        return (client or self.client).get(reverse('api:me')).json()['user']

    def registration_data(self, **changes):
        data = {
            'first_name': 'Charlie', 'last_name': 'Brown', 'username': 'charlie',
            'email': 'charlie@example.com',
            'password1': STRONG_PASSWORD, 'password2': STRONG_PASSWORD,
        }
        data.update(changes)
        return data


class MeAndCsrfTests(AuthApiTestCase):
    def test_guest_has_no_user(self):
        response = self.client.get(reverse('api:me'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'user': None})

    def test_logged_in_user_data(self):
        self.client.force_login(self.alice)

        self.assertEqual(
            self.me(),
            {'id': self.alice.id, 'username': 'alice', 'first_name': 'Alice',
             'last_name': '', 'email': 'alice@example.com'},
        )

    def test_csrf_endpoint_sets_the_cookie(self):
        response = self.client.get(reverse('api:csrf'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('csrftoken', response.cookies)


class LoginTests(AuthApiTestCase):
    def test_login(self):
        response = self.login()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user']['username'], 'alice')
        self.assertNotIn('password', response.json()['user'])
        self.assertEqual(self.me()['username'], 'alice')  # the session works

    def test_wrong_password(self):
        response = self.login(password='wrong')

        self.assertEqual(response.status_code, 400)
        self.assertIn('non_field_errors', response.json())
        self.assertIsNone(self.me())

    def test_missing_fields(self):
        response = self.post_json('api:login', {})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.json()), {'username', 'password'})

    def test_inactive_user_cannot_log_in(self):
        User.objects.filter(username='alice').update(is_active=False)

        self.assertEqual(self.login().status_code, 400)
        self.assertIsNone(self.me())

    def test_logout(self):
        self.login()

        response = self.client.post(reverse('api:logout'))

        self.assertEqual(response.status_code, 204)
        self.assertIsNone(self.me())

    def test_logout_of_a_guest_is_harmless(self):
        self.assertEqual(self.client.post(reverse('api:logout')).status_code, 204)

    def test_get_is_not_allowed(self):
        self.assertEqual(self.client.get(reverse('api:login')).status_code, 405)


class CartMergeTests(AuthApiTestCase):
    def add(self, product):
        return self.client.post(reverse('api:cart_items'), {'product_id': product.id})

    def test_guest_cart_moves_to_the_user_on_login(self):
        self.add(self.cpu)
        self.add(self.cpu)

        self.login()

        item = Cart.objects.get()
        self.assertEqual(item.user, self.alice)
        self.assertEqual(item.quantity, 2)
        cart = self.client.get(reverse('api:cart')).json()
        self.assertEqual(cart['total_quantity'], 2)

    def test_same_product_quantities_are_added(self):
        Cart.objects.create(user=self.alice, product=self.cpu, quantity=2)
        self.add(self.cpu)
        self.add(self.cpu)

        self.login()

        self.assertEqual(Cart.objects.get().quantity, 4)  # 2 + 2

    def test_merged_quantity_does_not_exceed_the_stock(self):
        Cart.objects.create(user=self.alice, product=self.cpu, quantity=4)
        self.add(self.cpu)
        self.add(self.cpu)

        self.login()

        self.assertEqual(Cart.objects.get().quantity, 5)  # 4 + 2 is more than 5 in stock

    def test_different_products_are_both_kept(self):
        Cart.objects.create(user=self.alice, product=self.cpu, quantity=1)
        self.add(self.mouse)

        self.login()

        products = sorted(Cart.objects.values_list('product__slug', flat=True))
        self.assertEqual(products, ['test-cpu', 'test-mouse'])
        self.assertEqual(Cart.objects.filter(user=self.alice).count(), 2)

    def test_other_guests_carts_are_not_touched(self):
        other_guest = Client()
        other_guest.post(reverse('api:cart_items'), {'product_id': self.mouse.id})
        self.add(self.cpu)

        self.login()

        self.assertIsNone(Cart.objects.get(product=self.mouse).user)
        self.assertEqual(Cart.objects.get(product=self.cpu).user, self.alice)


class RegisterTests(AuthApiTestCase):
    def test_register_creates_and_logs_in_the_user(self):
        response = self.post_json('api:register', self.registration_data())

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['user']['username'], 'charlie')
        user = User.objects.get(username='charlie')
        self.assertTrue(user.check_password(STRONG_PASSWORD))  # stored as a hash
        self.assertEqual(self.me()['username'], 'charlie')

    def test_guest_cart_moves_to_the_new_user(self):
        self.client.post(reverse('api:cart_items'), {'product_id': self.cpu.id})

        self.post_json('api:register', self.registration_data())

        self.assertEqual(Cart.objects.get().user, User.objects.get(username='charlie'))

    def test_wrong_data_is_rejected(self):
        cases = [
            ('password2', {'password2': 'different'}),  # the two passwords differ
            ('username', {'username': 'alice'}),  # already taken
            ('email', {'email': 'not an email'}),
            ('password2', {'password1': '123', 'password2': '123'}),  # too weak (Django reports it here)
            ('first_name', {'first_name': ''}),
        ]
        for field, changes in cases:
            with self.subTest(field=field, changes=changes):
                response = self.post_json('api:register', self.registration_data(**changes))

                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.json())

        self.assertFalse(User.objects.filter(username='charlie').exists())


class CsrfProtectionTests(AuthApiTestCase):
    """The test client skips the CSRF check unless it is asked to do it."""

    def setUp(self):
        self.strict = Client(enforce_csrf_checks=True)

    def test_login_without_a_token_is_rejected(self):
        response = self.login(client=self.strict)

        self.assertEqual(response.status_code, 403)
        self.assertIsNone(self.me(self.strict))

    def test_register_and_logout_without_a_token_are_rejected(self):
        response = self.post_json('api:register', self.registration_data(), self.strict)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username='charlie').exists())

        self.assertEqual(self.strict.post(reverse('api:logout')).status_code, 403)

    def test_login_with_the_token_from_the_csrf_endpoint(self):
        self.strict.get(reverse('api:csrf'))
        token = self.strict.cookies['csrftoken'].value

        response = self.post_json(
            'api:login', {'username': 'alice', 'password': 'pass12345'},
            self.strict, HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.me(self.strict)['username'], 'alice')

    def test_a_logged_in_user_needs_the_token_for_the_cart(self):
        self.strict.force_login(self.alice)
        url = reverse('api:cart_items')

        self.assertEqual(self.strict.post(url, {'product_id': self.cpu.id}).status_code, 403)

        self.strict.get(reverse('api:csrf'))
        token = self.strict.cookies['csrftoken'].value
        response = self.strict.post(url, {'product_id': self.cpu.id}, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
