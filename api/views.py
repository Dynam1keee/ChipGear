from rest_framework.generics import ListAPIView

from api.serializers import CategorySerializer
from goods.models import Category


class CategoryListView(ListAPIView):
    """GET /api/categories/ - all product categories."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = None  # there are only a few categories
