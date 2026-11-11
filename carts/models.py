from django.db import models

from goods.models import Product
from users.models import User

class CartQuerySet(models.QuerySet):
    def total_price(self):
        return sum(cart.products_price() for cart in self)
    
    def total_quantity(self):
        if self:
            return sum(cart.quantity for cart in self)
        
        return 0

class Cart(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, blank=True, null=True, verbose_name='User')
    product = models.ForeignKey(to=Product, on_delete=models.CASCADE, verbose_name='Product')
    quantity = models.PositiveSmallIntegerField(default=0, verbose_name='Quantity')
    session_key = models.CharField(max_length=32, null=True, blank=True)
    created_timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Date added')
    # is_abandoned = models.BooleanField(default=True, verbose_name='Abandoned')

    class Meta:
        db_table = 'cart'
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'

    objects = CartQuerySet().as_manager()

    def products_price(self):
        return round(self.product.sell_price() * self.quantity, 2)

    def __str__(self):
        if self.user:
            return f'User: {self.user.username} | Product: {self.product.name} | Quantity: {self.quantity}'

        return f'Abandoned cart | Product: {self.product.name} | Quantity: {self.quantity}'
    
# TODO: add CartItem
# class CartItem(models.Model):
#     cart = models.ForeignKey(to=Order, on_delete=models.CASCADE, verbose_name='Замовлення')
#     product = models.ForeignKey(to=Product, on_delete=models.SET_DEFAULT, null=True, verbose_name='Товар', default=None)
#     name = models.CharField(max_length=150, verbose_name='Назва')
#     price = models.DecimalField(max_digits=7, decimal_places=2, verbose_name='Ціна')
#     quantity = models.PositiveIntegerField(default=0, verbose_name='Кількість')
#     created_timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Дата продажу')

#     class Meta:
#         db_table = 'order_item'
#         verbose_name = 'Проданий товар'
#         verbose_name_plural = 'Продані товари'

#     objects = OrderItemQuerySet.as_manager()

#     def products_price(self):
#         return round(self.price * self.quantity, 2)
    
#     def __str__(self):
#         return f'Товар {self.name} | Замовлення № {self.order.pk}'