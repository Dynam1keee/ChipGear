from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from api.filters import build_facets, parse_filters, products_queryset
from api.serializers import CategorySerializer, ProductDetailSerializer, ProductSerializer
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
      category      category slug, for example "processors"
      q             search in the product name
      min_price     lowest price after discount
      max_price     highest price after discount
      manufacturer  manufacturer name; repeat it to choose several
      <spec>        a specification of the chosen category, for example
                    ?category=keyboards&layout=ANSI&backlighting=true;
                    repeat it to choose several values
      ordering      default | price | -price | name | -name
      page          page number

    Wrong values give a 400 response with the reason.
    """

    serializer_class = ProductSerializer

    def get_queryset(self):
        filters = parse_filters(self.request.query_params)
        products = products_queryset(filters)

        ordering = {
            'price': 'calculated_price',
            '-price': '-calculated_price',
            'name': 'name',
            '-name': '-name',
        }.get(filters.ordering)
        # Without ordering, the model default (by id) keeps pages stable
        if ordering:
            products = products.order_by(ordering, 'id')

        return products


class FilterFacetsView(APIView):
    """
    GET /api/filters/ - the options for the filter sidebar.

    Takes the same query parameters as /api/products/ and returns the price range,
    the manufacturers and (with a category) the specifications, each value with the
    number of products it would give.
    """

    def get(self, request):
        return Response(build_facets(parse_filters(request.query_params)))


class ProductDetailView(RetrieveAPIView):
    """GET /api/products/<slug>/ - one product with its specifications."""

    queryset = Product.objects.select_related('category')
    serializer_class = ProductDetailSerializer
    lookup_field = 'slug'
