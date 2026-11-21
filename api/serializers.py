from decimal import Decimal

from rest_framework import serializers

from carts.models import Cart
from goods.models import Category, Product
from orders.models import Order, OrderItem
from users.models import User


def image_url(image_field):
    """Return the relative URL of an image, or None if there is no image."""
    return image_field.url if image_field else None


class CategorySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image']

    def get_image(self, category):
        return image_url(category.image)


class ProductSerializer(serializers.ModelSerializer):
    """Product fields shown in lists."""

    category = serializers.SlugRelatedField(slug_field='slug', read_only=True)
    image = serializers.SerializerMethodField()
    # Price after the discount. It comes from Product.sell_price();
    # Decimal values are sent as strings ("90.00") to avoid rounding errors.
    sell_price = serializers.DecimalField(max_digits=7, decimal_places=2, read_only=True)
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'manufacturer', 'description', 'image',
            'price', 'discount', 'sell_price', 'quantity', 'in_stock', 'category',
        ]

    def get_image(self, product):
        return image_url(product.image)

    def get_in_stock(self, product):
        return product.quantity > 0


class ProductDetailSerializer(ProductSerializer):
    """Same as the list, plus the specifications of the product's category."""

    specs = serializers.SerializerMethodField()

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ['specs']

    def get_specs(self, product):
        # {"Socket": "LGA1700", ...}; empty if the product has no category model
        return product.get_values_dict() or {}


class ProductQuerySerializer(serializers.Serializer):
    """Validates the query string of GET /api/products/."""

    category = serializers.SlugField(required=False)
    q = serializers.CharField(required=False, allow_blank=True)
    min_price = serializers.DecimalField(required=False, max_digits=9, decimal_places=2, min_value=Decimal('0'))
    max_price = serializers.DecimalField(required=False, max_digits=9, decimal_places=2, min_value=Decimal('0'))
    manufacturer = serializers.ListField(child=serializers.CharField(), required=False)
    ordering = serializers.ChoiceField(
        required=False,
        choices=['default', 'price', '-price', 'name', '-name'],
    )


# --- cart -------------------------------------------------------------------

class CartProductSerializer(ProductSerializer):
    """The product inside a cart item: no long description."""

    class Meta(ProductSerializer.Meta):
        fields = [
            'id', 'name', 'slug', 'image', 'price', 'discount', 'sell_price',
            'quantity', 'in_stock', 'category',
        ]


class CartItemSerializer(serializers.ModelSerializer):
    product = CartProductSerializer()
    # price of this line: the price after discount times the quantity
    total = serializers.DecimalField(max_digits=10, decimal_places=2, source='products_price')

    class Meta:
        model = Cart
        fields = ['id', 'product', 'quantity', 'total']


class CartSerializer(serializers.Serializer):
    """The whole cart: used for every cart response."""

    items = CartItemSerializer(many=True)
    total_quantity = serializers.IntegerField()
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)


class ChangeQuantitySerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, max_value=32767)  # the limit of the database field


# --- users ------------------------------------------------------------------

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


# --- orders -----------------------------------------------------------------

class OrderItemSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'name', 'price', 'quantity', 'total']

    def get_total(self, item):
        return f'{item.products_price():.2f}'


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(source='orderitem_set', many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'created_timestamp', 'status', 'phone_number', 'requires_delivery',
            'delivery_address', 'payment_on_get', 'is_paid', 'items', 'total_price',
        ]

    def get_total_price(self, order):
        # orderitem_set is prefetched, so this does not make extra queries
        return f'{sum(item.products_price() for item in order.orderitem_set.all()):.2f}'


class CreateOrderSerializer(serializers.Serializer):
    phone_number = serializers.RegexField(
        r'^\d{10}$', error_messages={'invalid': 'Phone number must be 10 digits.'}
    )
    requires_delivery = serializers.BooleanField(default=False)
    delivery_address = serializers.CharField(required=False, allow_blank=True, default='')
    payment_on_get = serializers.BooleanField(default=False)

    def validate(self, data):
        if data['requires_delivery'] and not data['delivery_address'].strip():
            raise serializers.ValidationError({'delivery_address': ['Enter the delivery address.']})
        return data
