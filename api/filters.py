"""
Filtering of the catalog for the API.

The same query parameters are used by GET /api/products/ (the filtered list)
and GET /api/filters/ (the options for the filter sidebar with counters).
The logic follows the catalog view in goods/views.py.
"""
from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal
from math import ceil, floor

from django.apps import apps
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models
from django.db.models import ExpressionWrapper, F, FloatField, Max, Min, Value
from django.db.models.functions import Cast
from rest_framework import serializers

from api.serializers import ProductQuerySerializer
from goods.models import Category, Product

# Query parameters that have a fixed meaning. The specification fields of a
# category use their own names as parameters (for example ?socket=AM5),
# so none of them may be called like one of these.
RESERVED_PARAMS = {'category', 'q', 'min_price', 'max_price', 'manufacturer', 'ordering', 'page'}

INTEGER_MIN, INTEGER_MAX = -2147483648, 2147483647


def discounted_price():
    """Price after the discount, calculated in the database."""
    return ExpressionWrapper(
        Cast(F('price'), FloatField())
        * (Value(100.0) - Cast(F('discount'), FloatField()))
        / Value(100.0),
        output_field=FloatField(),
    )


def get_spec_fields(model_class):
    """The specification fields of a category model: {field name: field}."""
    product_fields = {f.name for f in Product._meta.fields}
    return {
        f.name: f
        for f in model_class._meta.fields
        if f.name not in product_fields and not f.name.endswith('_ptr')
    }


def parse_spec_value(model_field, raw):
    """Convert a text value from the address to the type of the model field."""
    if isinstance(model_field, models.BooleanField):
        value = raw.strip().lower()
        if value in ('true', '1'):
            return True
        if value in ('false', '0'):
            return False
        raise DjangoValidationError('Invalid yes/no value.')

    value = model_field.to_python(raw)
    if isinstance(model_field, models.IntegerField) and not INTEGER_MIN <= value <= INTEGER_MAX:
        raise DjangoValidationError('Number out of range.')
    return value


@dataclass
class CatalogFilters:
    model: type = Product  # the model of the category, or Product for the whole catalog
    category: Category | None = None
    q: str = ''
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    manufacturers: list = field(default_factory=list)
    specs: dict = field(default_factory=dict)  # {field name: [values of the right type]}
    spec_fields: dict = field(default_factory=dict)  # {field name: model field} of the category
    ordering: str | None = None


def parse_filters(query_params):
    """Validate the query string. Wrong values raise a ValidationError (HTTP 400)."""
    serializer = ProductQuerySerializer(data=query_params)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    filters = CatalogFilters(
        q=data.get('q', ''),
        min_price=data.get('min_price'),
        max_price=data.get('max_price'),
        manufacturers=data.get('manufacturer', []),
        ordering=data.get('ordering'),
    )

    if 'category' in data:
        category = Category.objects.filter(slug=data['category']).first()
        if category is None:
            raise serializers.ValidationError({'category': 'Unknown category.'})
        try:
            filters.model = apps.get_model('goods', category.model_name)
        except LookupError:
            raise serializers.ValidationError({'category': 'This category has no product model.'})
        filters.category = category
        filters.spec_fields = get_spec_fields(filters.model)

    errors = {}
    for name, model_field in filters.spec_fields.items():
        raw_values = query_params.getlist(name)
        if not raw_values:
            continue
        try:
            filters.specs[name] = [parse_spec_value(model_field, raw) for raw in raw_values]
        except DjangoValidationError:
            errors[name] = 'Invalid value.'
    if errors:
        raise serializers.ValidationError(errors)

    return filters


# --- applying the filters ---------------------------------------------------

def apply_search(queryset, filters):
    if filters.q:
        queryset = queryset.filter(name__icontains=filters.q)
    return queryset


def apply_price(queryset, filters):
    if filters.min_price is not None:
        queryset = queryset.filter(calculated_price__gte=float(filters.min_price))
    if filters.max_price is not None:
        queryset = queryset.filter(calculated_price__lte=float(filters.max_price))
    return queryset


def apply_manufacturers(queryset, filters):
    if filters.manufacturers:
        queryset = queryset.filter(manufacturer__in=filters.manufacturers)
    return queryset


def apply_specs(queryset, filters, skip=None):
    """Filter by the chosen specifications; `skip` leaves one specification out."""
    for name, values in filters.specs.items():
        if name != skip:
            queryset = queryset.filter(**{f'{name}__in': values})
    return queryset


def products_queryset(filters):
    """The products that match all the filters."""
    queryset = (
        filters.model.objects
        .select_related('category')
        .annotate(calculated_price=discounted_price())
    )
    queryset = apply_price(apply_search(queryset, filters), filters)
    return apply_specs(apply_manufacturers(queryset, filters), filters)


# --- options of the filter sidebar --------------------------------------------

def distinct_values(model, name):
    values = model.objects.order_by(name).values_list(name, flat=True).distinct()
    return [value for value in values if value is not None]


def sorted_options(counts, values):
    """All values, the most frequent first, then in alphabetical order."""
    options = [{'value': value, 'count': counts.get(value, 0)} for value in values]
    return sorted(options, key=lambda option: (-option['count'], str(option['value']).lower()))


def get_price_range(queryset, fallback):
    """Lowest and highest price after discount; the fallback is used if nothing was found."""
    for candidates in (queryset, fallback):
        result = candidates.aggregate(low=Min('calculated_price'), high=Max('calculated_price'))
        if result['low'] is not None:
            return {'min': floor(result['low']), 'max': ceil(result['high'])}
    return {'min': 0, 'max': 0}


def build_facets(filters):
    """
    Options for the sidebar. Every group of filters is counted with all the OTHER
    filters applied, so the user sees how many products each choice would give.
    """
    everything = filters.model.objects.annotate(calculated_price=discounted_price())
    searched = apply_search(everything, filters)

    # The price range is calculated before the price filter, so the sliders keep their limits
    price_range = get_price_range(searched, fallback=everything)
    facet_base = apply_price(searched, filters)

    manufacturer_counts = Counter(
        apply_specs(facet_base, filters).values_list('manufacturer', flat=True)
    )
    manufacturers = sorted_options(
        manufacturer_counts, distinct_values(filters.model, 'manufacturer')
    )

    specs = []
    for name, model_field in filters.spec_fields.items():
        facet_goods = apply_specs(apply_manufacturers(facet_base, filters), filters, skip=name)
        counts = Counter(facet_goods.values_list(name, flat=True))
        specs.append({
            'name': name,
            'label': str(model_field.verbose_name),
            'values': sorted_options(counts, distinct_values(filters.model, name)),
        })
    specs.sort(key=lambda spec: spec['label'])

    return {'price_range': price_range, 'manufacturers': manufacturers, 'specs': specs}
