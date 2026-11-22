from django.test import TestCase
from django.urls import reverse

from goods.models import Category, Product
from orders.models import Order, OrderItem
from users.models import User


class OrderAdminTests(TestCase):
    """The admin pages of orders must open even for an order without a user (a guest or a deleted account)."""

    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name='Mice', slug='mice', model_name='Mouse')
        cls.product = Product.objects.create(
            name='Mouse', slug='mouse', manufacturer='Acme', price=10, discount=0, quantity=5, category=category,
        )
        cls.admin = User.objects.create_superuser(username='boss', password='pass12345', email='boss@example.com')
        cls.guest_order = Order.objects.create(user=None, phone_number='0501234567')
        OrderItem.objects.create(order=cls.guest_order, product=cls.product, name='Mouse', price=10, quantity=1)
        named = User.objects.create_user(username='alice', password='pass12345', first_name='Alice', last_name='Smith')
        cls.named_order = Order.objects.create(user=named, phone_number='0501234567')

    def test_str_of_an_order_without_a_user(self):
        self.assertEqual(str(self.guest_order), f'Order # {self.guest_order.pk} | Customer: Guest')
        self.assertIn('Order #', str(OrderItem.objects.get()))

    def test_str_of_an_order_with_a_user(self):
        self.assertEqual(str(self.named_order), f'Order # {self.named_order.pk} | Customer: Alice Smith')

    def test_user_without_a_name_is_shown_by_username(self):
        bare = Order.objects.create(user=User.objects.create_user(username='bare', password='pass12345'), phone_number='0501234567')
        self.assertEqual(str(bare), f'Order # {bare.pk} | Customer: bare')

    def test_admin_lists_open(self):
        self.client.force_login(self.admin)
        for name in ('admin:orders_order_changelist', 'admin:orders_orderitem_changelist'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        self.assertEqual(self.client.get(reverse('admin:orders_order_change', args=[self.guest_order.pk])).status_code, 200)
