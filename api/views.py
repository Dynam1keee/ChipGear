from django.db.models import ExpressionWrapper, F, FloatField, Value
from django.db.models.functions import Cast
from rest_framework.generics import ListAPIView, RetrieveAPIView

from api.serializers import (
    CategorySerializer,
    ProductDetailSerializer,
    ProductQuerySerializer,
    ProductSerializer,
)
from goods.models import Category, Product


class CategoryListView(ListAPIView):
    """GET /api/categories/ - all product categories."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = None  # there are only a few categories


class ProductListView(ListAPIView):
    """
    GET /api/products/ - paginated list of products.

    Query parameters (all optional):
      category   category slug, for example "processors"
      q          search in the product name
      min_price  lowest price after discount
      max_price  highest price after discount
      ordering   default | price | -price | name | -name
      page       page number
    """

    serializer_class = ProductSerializer

    def get_queryset(self):
        # Bad query parameters give a 400 response with the reason
        params = ProductQuerySerializer(data=self.request.query_params)
        params.is_valid(raise_exception=True)
        filters = params.validated_data

        # Price after discount, calculated in the database (same formula as the catalog)
        discounted_price = ExpressionWrapper(
            Cast(F('price'), FloatField())
            * (Value(100.0) - Cast(F('discount'), FloatField()))
            / Value(100.0),
            output_field=FloatField(),
        )

        products = Product.objects.select_related('category').annotate(
            calculated_price=discounted_price
        )

        if 'category' in filters:
            products = products.filter(category__slug=filters['category'])
        if filters.get('q'):
            products = products.filter(name__icontains=filters['q'])
        if 'min_price' in filters:
            products = products.filter(calculated_price__gte=float(filters['min_price']))
        if 'max_price' in filters:
            products = products.filter(calculated_price__lte=float(filters['max_price']))

        ordering = {
            'price': 'calculated_price',
            '-price': '-calculated_price',
            'name': 'name',
            '-name': '-name',
        }.get(filters.get('ordering'))
        # Without ordering, the model default (by id) keeps pages stable
        if ordering:
            products = products.order_by(ordering, 'id')

        return products


class ProductDetailView(RetrieveAPIView):
    """GET /api/products/<slug>/ - one product with its specifications."""

    queryset = Product.objects.select_related('category')
    serializer_class = ProductDetailSerializer
    lookup_field = 'slug'
