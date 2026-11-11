from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.shortcuts import HttpResponse

from django.http import Http404, JsonResponse
from django.urls import reverse
from goods.models import Product, Category
from django.core.paginator import Paginator

from goods.utils import q_search

from goods.forms import ProductFilterForm

from collections import Counter

from orders.models import OrderItem
from django.db.models import IntegerField, OuterRef, Subquery, Sum, Count, Case, Value, When

def index(request):
    # Підраховуємо кількість проданих продуктів і групуємо їх за ідентифікатором продукту
    product_sales = OrderItem.objects.values('product').filter(product__quantity__gt=0).annotate(total_sales=Sum('quantity')).order_by('-total_sales')[:18]

    # Отримуємо ідентифікатори найчастіше продаються товарів
    best_selling_product_ids = [item['product'] for item in product_sales]

    # Отримуємо об'єкти найчастіше продаються товарів
    preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(best_selling_product_ids)])
    best_selling_products = Product.objects.filter(pk__in=best_selling_product_ids).order_by(preserved_order)
    
    context = {
        'title': 'ChipGear - Home',
        'top_goods': best_selling_products
    }
    return render(request, 'main/index.html', context)

def about(request):
    context = {
        'title': 'ChipGear - About us',
    }
    return render(request, 'main/about.html', context)