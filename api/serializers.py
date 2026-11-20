from decimal import Decimal

from rest_framework import serializers

from goods.models import Category, Product


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
