from django.utils import timezone
from django.http import Http404, JsonResponse
from django.shortcuts import render, get_object_or_404
from goods.models import Product, Category, RecentlyViewed
from orders.models import OrderItem
from django.core.paginator import Paginator

from goods.utils import q_search

from .forms import ProductFilterForm

from collections import Counter
from django.db.models import Count, IntegerField, Min, Max, F, OuterRef, Subquery, Sum, Value, FloatField, ExpressionWrapper
from django.db.models.functions import Cast, Coalesce
from django.db import models
from math import floor, ceil
from django.apps import apps
from django.urls import reverse


def get_search_suggestions(request):
    """Повертає до чотирьох товарів для пошукових підказок."""

    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()

    if len(query) < 2:
        return JsonResponse({'results': []})

    # Кількість проданих одиниць кожного товару.
    sales_subquery = (
        OrderItem.objects
        .filter(product=OuterRef('pk'))
        .values('product')
        .annotate(total=Sum('quantity'))
        .values('total')[:1]
    )

    # Пошук товарів за назвою серед товарів у наявності.
    products = Product.objects.filter(
        name__icontains=query,
        quantity__gt=0,
    ).select_related('category')

    # За потреби обмежуємо пошук вибраною категорією.
    if category_slug and category_slug != 'all':
        products = products.filter(category__slug=category_slug)

    # Спочатку популярніші товари, потім сортування за назвою.
    products = (
        products
        .annotate(
            total_sales=Coalesce(
                Subquery(
                    sales_subquery,
                    output_field=IntegerField(),
                ),
                Value(0),
            )
        )
        .order_by('-total_sales', 'name')[:4]
    )

    results = []

    for product in products:
        try:
            image_url = product.image.url
        except (ValueError, AttributeError):
            image_url = ''

        results.append({
            'name': product.name,
            'image': image_url,
            'url': reverse(
                'catalog:product',
                args=[
                    product.category.slug,
                    product.slug,
                ],
            ),
        })

    return JsonResponse({'results': results})


def get_price_range(goods, discounted_price, fallback_goods=None):
    """Обчислює мінімальну та максимальну ціну товарів."""

    price_range = goods.aggregate(
        min_price=Min(discounted_price),
        max_price=Max(discounted_price),
    )

    # Якщо пошук нічого не знайшов, можна використати
    # загальний діапазон цін категорії або всього каталогу.
    if price_range['min_price'] is None and fallback_goods is not None:
        price_range = fallback_goods.aggregate(
            min_price=Min(discounted_price),
            max_price=Max(discounted_price),
        )

    if price_range['min_price'] is None:
        return {
            'min_price': 0,
            'max_price': 0,
        }

    return {
        'min_price': floor(price_range['min_price']),
        'max_price': ceil(price_range['max_price']),
    }


def catalog(request, category_slug=None):
    # --------------------------------------------------
    # 1. ПОШУКОВІ ПІДКАЗКИ
    # --------------------------------------------------

    if request.GET.get('suggestions') == '1':
        return get_search_suggestions(request)

    # --------------------------------------------------
    # 2. ПОЧАТКОВІ ЗНАЧЕННЯ
    # --------------------------------------------------

    page = request.GET.get('page', 1)
    query = request.GET.get('q')
    price_order = request.GET.get('price_order')

    category = None
    model_class = None
    names = []
    selected = []
    fields_info = []
    page_name = 'Catalog'

    # --------------------------------------------------
    # 3. ВИБІР ТОВАРІВ І КАТЕГОРІЇ
    # --------------------------------------------------

    if category_slug:
        category = get_object_or_404(
            Category,
            slug=category_slug,
        )

        model_class = apps.get_model(
            'goods',
            category.model_name,
        )

        goods = model_class.objects.all()
        page_name = model_class._meta.verbose_name_plural

        category_all_specs = {
            field.name: field.verbose_name
            for field in model_class._meta.fields
            if not field.name.endswith('_ptr')
        }

        products_specs = {
            field.name
            for field in Product._meta.fields
        }

        names = list(
            set(category_all_specs) - products_specs
        )

    else:
        goods = Product.objects.all()

    # --------------------------------------------------
    # 4. ПОШУК ЗА НАЗВОЮ
    # --------------------------------------------------

    if query:
        goods = goods.filter(name__icontains=query)
        page_name = f'Search results for query "{query}"'

    filter_form = ProductFilterForm(request.GET)

    # --------------------------------------------------
    # 5. РОЗРАХУНОК ЦІНИ ЗІ ЗНИЖКОЮ
    # --------------------------------------------------

    discounted_price = ExpressionWrapper(
        Cast(F('price'), output_field=FloatField())
        * (
            Value(100.0)
            - Cast(F('discount'), output_field=FloatField())
        )
        / Value(100.0),
        output_field=FloatField(),
    )

    # --------------------------------------------------
    # 6. ВАЛІДАЦІЯ ФОРМИ ТА ФІЛЬТРАЦІЯ
    # --------------------------------------------------

    if filter_form.is_valid():

        # Додатковий пошук за назвою з форми.
        if filter_form.cleaned_data['name']:
            goods = goods.filter(
                name__icontains=filter_form.cleaned_data['name']
            )

        # Діапазон цін визначається до фільтрації за ціною.
        # Якщо результатів немає, використовуємо загальний
        # діапазон відповідної категорії або каталогу.
        fallback_goods = (
            model_class.objects.all()
            if model_class
            else Product.objects.all()
        )

        price_range = get_price_range(
            goods,
            discounted_price,
            fallback_goods=fallback_goods,
        )

        # Додаємо розраховану ціну зі знижкою.
        goods = goods.annotate(
            calculated_price=discounted_price,
        )

        # Мінімальна ціна.
        if filter_form.cleaned_data['min_price'] is not None:
            goods = goods.filter(
                calculated_price__gte=
                filter_form.cleaned_data['min_price']
            )

        # Максимальна ціна.
        if filter_form.cleaned_data['max_price'] is not None:
            goods = goods.filter(
                calculated_price__lte=
                filter_form.cleaned_data['max_price']
            )

        # Базовий QuerySet для фасетів:
        # після пошуку та цінової фільтрації,
        # але до фільтрації за виробником і характеристиками.
        goods_for_facets = goods

        checked_manufacturers = request.GET.getlist(
            'manufacturer'
        )

        checked_specs = {
            name: request.GET.getlist(name)
            for name in names
        }

        # Фільтр за виробником.
        if checked_manufacturers:
            goods = goods.filter(
                manufacturer__in=checked_manufacturers
            )
            selected.extend(checked_manufacturers)

        # Фільтри за характеристиками.
        for spec, values in checked_specs.items():
            if values:
                goods = goods.filter(
                    **{f'{spec}__in': values}
                )
                selected.extend(values)

    else:
        # Для невалідної форми діапазон обчислюється
        # на основі початкового QuerySet без fallback.
        price_range = get_price_range(
            goods,
            discounted_price,
        )

        goods_for_facets = goods

        checked_manufacturers = request.GET.getlist(
            'manufacturer'
        )

        checked_specs = {
            name: request.GET.getlist(name)
            for name in names
        }

    # --------------------------------------------------
    # 7. ФАСЕТИ: КІЛЬКІСТЬ ТОВАРІВ ЗА ВИРОБНИКАМИ
    # --------------------------------------------------

    manufacturer_goods = goods_for_facets

    # Для підрахунку виробників враховуємо характеристики,
    # але не застосовуємо фільтр за самим виробником.
    for spec, values in checked_specs.items():
        if values:
            manufacturer_goods = manufacturer_goods.filter(
                **{f'{spec}__in': values}
            )

    manufacturer_counts = Counter(
        manufacturer_goods.values_list(
            'manufacturer',
            flat=True,
        )
    )

    # Усі виробники, наявні в базі даних для цієї моделі.
    all_manufacturers = (
        model_class.objects
        if model_class
        else Product.objects
    )

    all_manufacturers = all_manufacturers.values_list(
        'manufacturer',
        flat=True,
    ).distinct()

    manufacturer_values = {
        value: manufacturer_counts.get(value, 0)
        for value in all_manufacturers
        if value is not None
    }

    fields_info = [
        [
            'manufacturer',
            'Manufacturer',
            dict(sorted(
                manufacturer_values.items(),
                key=lambda item: item[1],
                reverse=True,
            )),
        ],
    ]

    # --------------------------------------------------
    # 8. ФАСЕТИ: ХАРАКТЕРИСТИКИ КАТЕГОРІЇ
    # --------------------------------------------------

    if category_slug:
        for name in names:
            vname = model_class._meta.get_field(
                name
            ).verbose_name

            facet_goods = goods_for_facets

            # Для характеристики враховуємо вибраних
            # виробників та інші характеристики.
            if checked_manufacturers:
                facet_goods = facet_goods.filter(
                    manufacturer__in=checked_manufacturers
                )

            for other_name, values in checked_specs.items():
                if other_name != name and values:
                    facet_goods = facet_goods.filter(
                        **{f'{other_name}__in': values}
                    )

            # Кількість товарів для кожного значення.
            values_counts = Counter(
                facet_goods.values_list(name, flat=True)
            )

            # Усі можливі значення характеристики.
            all_values = (
                model_class.objects
                .values_list(name, flat=True)
                .distinct()
            )

            value_counts = {
                value: values_counts.get(value, 0)
                for value in all_values
                if value is not None
            }

            # Спочатку значення, які зустрічаються частіше.
            value_counts = dict(sorted(
                value_counts.items(),
                key=lambda item: item[1],
                reverse=True,
            ))

            fields_info.append([
                name,
                vname,
                value_counts,
            ])

        # Сортуємо характеристики за назвою.
        fields_info = [fields_info[0]] + sorted(
            fields_info[1:],
            key=lambda item: item[1],
        )

    # --------------------------------------------------
    # 9. СОРТУВАННЯ ТА ПАГІНАЦІЯ
    # --------------------------------------------------

    # Додаємо розраховану ціну незалежно від валідності форми.
    # Це гарантує наявність поля для сортування.
    goods = goods.annotate(
        calculated_price=discounted_price,
    )

    if price_order == 'price':
        goods = goods.order_by('calculated_price')

    elif price_order == '-price':
        goods = goods.order_by('-calculated_price')

    elif price_order and price_order != 'default':
        # Дозволяємо інші поля сортування, якщо вони є
        # реальними полями моделі.
        allowed_fields = {
            field.name
            for field in Product._meta.fields
        }

        sort_field = price_order.lstrip('-')

        if sort_field in allowed_fields:
            goods = goods.order_by(price_order)

    goods_count = goods.count()

    if goods_count > 0:
        paginator = Paginator(goods, 20)
        current_page = paginator.get_page(page)
        goods_for_template = current_page
    else:
        goods_for_template = []

    # --------------------------------------------------
    # 10. КОНТЕКСТ І ВІДПОВІДЬ
    # --------------------------------------------------

    context = {
        'title': f'ChipGear - {page_name}',
        'goods': goods_for_template,
        'slug_url': category_slug,
        'category': page_name,
        'category_name': category,
        'price_range': price_range,
        'goods_count': goods_count,
        'filter_form': filter_form,
        'fields_info': fields_info,
        'selected': selected,
    }

    return render(
        request,
        'goods/catalog.html',
        context,
    )

def product(request, category_slug, product_slug):
    product = get_object_or_404(Product, slug=product_slug)

    # ВІДОБРАЖЕННЯ ІСТОРІЇ ПЕРЕГЛЯДУ ТОВАРІВ
    # Якщо користувач авторизований, зберегти переглянутий товар
    if request.user.is_authenticated:
        recently_viewed, created = RecentlyViewed.objects.get_or_create(user=request.user, product=product)
        if not created:
            recently_viewed.viewed_at = timezone.now()
            recently_viewed.save()
    else:
        products_history = request.session.get('viewed_products', [])
        # Додати поточний продукт у список переглянутих, якщо його ще немає
        if product.id not in products_history:
            products_history.append(product.id)
            # Зберегти оновлений список у сесії
            request.session['viewed_products'] = products_history

    recently_viewed_products = []
    if request.user.is_authenticated:
        recently_viewed_products = Product.objects.filter(recentlyviewed__user=request.user).exclude(id=product.id).order_by('-recentlyviewed__viewed_at')
    else:
        recently_viewed_products = Product.objects.filter(id__in=products_history).exclude(id=product.id).order_by('-recentlyviewed__viewed_at')
    
    # ВІДОБРАЖЕННЯ ПОВ'ЯЗАНИХ ТОВАРІВ
    # Отримати всі товари, які купуються разом із поточним товаром
    orders_with_product = OrderItem.objects.filter(product_id=product.id).values_list('order_id', flat=True)
    related_product_ids = OrderItem.objects.filter(order_id__in=orders_with_product) \
                                            .exclude(product_id=product.id) \
                                            .values('product_id') \
                                            .annotate(total=Count('product_id')) \
                                            .order_by('-total') \
                                            .values_list('product_id', flat=True)[:10] # кількість товарів, які будуть відображатися
    
    related_products = Product.objects.filter(id__in=related_product_ids)

    context = {
        'title': f'{product} - ChipGear',
        'product': product,
        'related_products': related_products,
        'recently_viewed_products': recently_viewed_products
    }

    return render(request, "goods/product.html", context)
