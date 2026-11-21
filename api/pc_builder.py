"""
PC builder API (only for logged in users). The rules of compatibility are in builder/rules.py.

Every answer about the build looks like this:
{"slots": {"cpu": {product} or null, ...}, "problems": [{"slots": [...], "message": "..."}],
 "total_price": "123.00", "estimated_power": 575 or null, "recommended_psu": 690 or null}

GET    /api/builder/                      - the build of the user
DELETE /api/builder/                      - clear the build
PUT    /api/builder/<slot>/ {"product_id": 5}  - put a part into a slot (it must fit the other parts)
DELETE /api/builder/<slot>/               - empty the slot
GET    /api/builder/<slot>/options/       - the parts for the slot, each with "compatible" and "reasons"
                                            (?only_compatible=true leaves only the fitting parts)
POST   /api/builder/add-to-cart/          - put all parts of the build into the cart
"""
from decimal import Decimal

from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.cart import cart_response
from api.serializers import AddToCartSerializer, ProductSerializer
from builder import rules
from builder.models import Build
from carts.models import Cart
from goods import models as goods_models


def get_build(user):
    build, _ = Build.objects.get_or_create(user=user)
    return build


def parts_of(build):
    """{slot: part} for the slots that are not empty."""
    return {slot: getattr(build, slot) for slot in rules.SLOTS if getattr(build, slot) is not None}


def model_of(slot):
    if slot not in rules.SLOT_MODELS:
        raise Http404('Unknown slot.')
    return getattr(goods_models, rules.SLOT_MODELS[slot])


def not_available_reason(part):
    return 'This product is out of stock.' if part.quantity < 1 else None


def build_response(build, status=200):
    build = Build.objects.select_related(*rules.SLOTS).get(pk=build.pk)
    parts = parts_of(build)
    has_load = 'cpu' in parts or 'gpu' in parts
    load = rules.estimated_load(parts) if has_load else None

    data = {
        'slots': {slot: ProductSerializer(parts[slot]).data if slot in parts else None for slot in rules.SLOTS},
        'problems': [
            {'slots': list(problem.slots), 'message': problem.message}
            for problem in rules.find_problems(parts)
        ],
        'total_price': f'{sum((part.sell_price() for part in parts.values()), Decimal("0")):.2f}',
        'estimated_power': load,
        'recommended_psu': round(load * rules.PSU_MARGIN) if load else None,
    }
    return Response(data, status=status)


class BuildView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return build_response(get_build(request.user))

    def delete(self, request):
        build = get_build(request.user)
        for slot in rules.SLOTS:
            setattr(build, slot, None)
        build.save()
        return build_response(build)


class BuildSlotView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, slot):
        model = model_of(slot)
        data = AddToCartSerializer(data=request.data)  # the same body: {"product_id": 5}
        data.is_valid(raise_exception=True)

        # The id of a CPU is the id of its product, so a product of another kind is "not found"
        part = get_object_or_404(model, id=data.validated_data['product_id'])
        build = get_build(request.user)

        reasons = [not_available_reason(part)] if not_available_reason(part) else []
        reasons += rules.check_candidate(slot, part, parts_of(build))
        if reasons:
            raise serializers.ValidationError({'non_field_errors': reasons})

        setattr(build, slot, part)
        build.save()
        return build_response(build)

    def delete(self, request, slot):
        model_of(slot)  # 404 for an unknown slot
        build = get_build(request.user)
        setattr(build, slot, None)
        build.save()
        return build_response(build)


class SlotOptionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, slot):
        model = model_of(slot)
        parts = parts_of(get_build(request.user))
        only_compatible = request.query_params.get('only_compatible', '').lower() in ('1', 'true')

        options = []
        for part in model.objects.select_related('category').order_by('id'):
            reasons = [not_available_reason(part)] if not_available_reason(part) else []
            reasons += rules.check_candidate(slot, part, parts)
            if only_compatible and reasons:
                continue
            options.append({**ProductSerializer(part).data, 'compatible': not reasons, 'reasons': reasons})
        return Response(options)


class AddBuildToCartView(APIView):
    """POST /api/builder/add-to-cart/ - one piece of every part goes to the cart of the user."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        parts = parts_of(get_build(request.user))
        if not parts:
            raise serializers.ValidationError({'non_field_errors': ['The build is empty.']})

        problems = rules.find_problems(parts)
        if problems:
            raise serializers.ValidationError({'non_field_errors': [problem.message for problem in problems]})

        with transaction.atomic():
            for part in parts.values():
                item = Cart.objects.filter(user=request.user, product_id=part.id).first()
                new_quantity = item.quantity + 1 if item else 1
                if new_quantity > part.quantity:
                    raise serializers.ValidationError(
                        {'non_field_errors': [f'Not enough "{part.name}" in stock.']}
                    )
                if item:
                    item.quantity = new_quantity
                    item.save()
                else:
                    Cart.objects.create(user=request.user, product_id=part.id, quantity=1)

        return cart_response(request)
