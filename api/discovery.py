"""
Product discovery for the home page and the product page.

GET  /api/top-sales/                 - the best selling products (empty until there are enough sales)
GET  /api/products/<slug>/related/   - products that are bought together with this one
POST /api/products/<slug>/view/      - remember that the current visitor has opened this product
GET  /api/recently-viewed/           - the products the visitor has opened lately, the newest first
                                       (?exclude=<slug> leaves one product out)

Recently viewed products of a logged in user are kept in the database (RecentlyViewed),
the ones of a guest in the session.
"""
from django.db.models import Case, Count, IntegerField, Sum, When
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import ProductSerializer
from goods.models import Product, RecentlyViewed
from orders.models import OrderItem

# The top sales block appears only when at least this many different
# products (in stock) have been sold; until then the list is empty.
TOP_SALES_MIN_PRODUCTS = 6
TOP_SALES_LIMIT = 12
RELATED_LIMIT = 10
HISTORY_LIMIT = 12
HISTORY_KEEP = 30  # how many viewed products are remembered for one visitor
SESSION_KEY = 'viewed_products'


def in_given_order(ids):
    """Order products like the list of ids (a database query does not keep the order)."""
    return Case(*[When(pk=pk, then=position) for position, pk in enumerate(ids)], output_field=IntegerField())


def products_by_ids(ids):
    if not ids:
        return Product.objects.none()
    return Product.objects.filter(pk__in=ids).select_related('category').order_by(in_given_order(ids))


class TopSalesView(APIView):
    def get(self, request):
        sold = list(
            OrderItem.objects
            .filter(product__isnull=False, product__quantity__gt=0)
            .values('product')
            .annotate(total=Sum('quantity'))
            .order_by('-total', 'product')
            .values_list('product', flat=True)
        )
        if len(sold) < TOP_SALES_MIN_PRODUCTS:
            return Response([])
        products = products_by_ids(sold[:TOP_SALES_LIMIT])
        return Response(ProductSerializer(products, many=True).data)


class RelatedProductsView(APIView):
    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        order_ids = OrderItem.objects.filter(product=product).values('order_id')
        related = list(
            OrderItem.objects
            .filter(order_id__in=order_ids, product__isnull=False, product__quantity__gt=0)
            .exclude(product=product)
            .values('product')
            .annotate(total=Count('id'))
            .order_by('-total', 'product')
            .values_list('product', flat=True)[:RELATED_LIMIT]
        )
        return Response(ProductSerializer(products_by_ids(related), many=True).data)


def viewed_ids(request):
    """The ids of the viewed products of this visitor, the newest first."""
    if request.user.is_authenticated:
        return list(
            RecentlyViewed.objects.filter(user=request.user)
            .order_by('-viewed_at', '-id')
            .values_list('product_id', flat=True)
        )
    return list(request.session.get(SESSION_KEY, []))


class ViewProductView(APIView):
    def post(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        if request.user.is_authenticated:
            # The old record is replaced by a new one: its id is the biggest, so the order is right
            # even when two views get the same time (the clock of some systems is not precise)
            RecentlyViewed.objects.filter(user=request.user, product=product).delete()
            RecentlyViewed.objects.create(user=request.user, product=product)
            old = RecentlyViewed.objects.filter(user=request.user).order_by('-viewed_at', '-id')[HISTORY_KEEP:]
            RecentlyViewed.objects.filter(pk__in=[row.pk for row in old]).delete()
        else:
            ids = [pk for pk in request.session.get(SESSION_KEY, []) if pk != product.pk]
            request.session[SESSION_KEY] = ([product.pk] + ids)[:HISTORY_KEEP]
        return Response(status=204)


class RecentlyViewedView(APIView):
    def get(self, request):
        ids = viewed_ids(request)
        exclude = request.query_params.get('exclude')
        if exclude:
            skip = Product.objects.filter(slug=exclude).values_list('pk', flat=True).first()
            ids = [pk for pk in ids if pk != skip]
        products = products_by_ids(ids[:HISTORY_LIMIT])
        return Response(ProductSerializer(products, many=True).data)
