"""
Cart API. Every response is the whole cart:
{"items": [...], "total_quantity": 3, "total_price": "270.00"}

Guests have a cart tied to their session cookie, logged in users have a cart
tied to their account. A user can only see and change their own cart.
"""
from decimal import Decimal

from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import AddToCartSerializer, CartSerializer, ChangeQuantitySerializer
from carts.models import Cart
from carts.utils import get_user_carts
from goods.models import Product


def user_cart_items(request):
    # get_user_carts() also creates a session for a new guest
    return get_user_carts(request).select_related('product__category').order_by('id')


def cart_response(request):
    items = list(user_cart_items(request))
    cart = {
        'items': items,
        'total_quantity': sum(item.quantity for item in items),
        'total_price': sum((item.products_price() for item in items), Decimal('0')),
    }
    return Response(CartSerializer(cart).data)


class CartView(APIView):
    """GET /api/cart/ - the current cart."""

    def get(self, request):
        return cart_response(request)


class CartItemListView(APIView):
    """POST /api/cart/items/ {"product_id": 5} - add one piece of the product."""

    def post(self, request):
        data = AddToCartSerializer(data=request.data)
        data.is_valid(raise_exception=True)

        product = get_object_or_404(Product, id=data.validated_data['product_id'])
        item = user_cart_items(request).filter(product=product).first()
        new_quantity = item.quantity + 1 if item else 1

        if new_quantity > product.quantity:
            raise serializers.ValidationError({'product_id': 'Not enough items in stock.'})

        if item:
            item.quantity = new_quantity
            item.save()
        elif request.user.is_authenticated:
            Cart.objects.create(user=request.user, product=product, quantity=1)
        else:
            Cart.objects.create(session_key=request.session.session_key, product=product, quantity=1)

        return cart_response(request)


class CartItemDetailView(APIView):
    """
    PATCH  /api/cart/items/<id>/ {"quantity": 3} - set the quantity
    DELETE /api/cart/items/<id>/                 - remove the item
    """

    def get_item(self, request, item_id):
        # Only the items of the current user or guest are searched: other
        # people's items give 404, so nobody can change them by guessing ids
        return get_object_or_404(user_cart_items(request), id=item_id)

    def patch(self, request, item_id):
        data = ChangeQuantitySerializer(data=request.data)
        data.is_valid(raise_exception=True)

        item = self.get_item(request, item_id)
        quantity = data.validated_data['quantity']
        if quantity > item.product.quantity:
            raise serializers.ValidationError({'quantity': 'Not enough items in stock.'})

        item.quantity = quantity
        item.save()
        return cart_response(request)

    def delete(self, request, item_id):
        self.get_item(request, item_id).delete()
        return cart_response(request)
