"""
Orders API (only for logged in users).

GET  /api/orders/ - the orders of the current user, the newest first
POST /api/orders/ {"phone_number": "0501234567", "requires_delivery": true,
                   "delivery_address": "...", "payment_on_get": false}
     - creates an order from the cart, takes the products from the stock and clears the cart
"""
from django.db import transaction
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import CreateOrderSerializer, OrderSerializer
from carts.models import Cart
from goods.models import Product
from orders.models import Order, OrderItem


def user_orders(user):
    return Order.objects.filter(user=user).prefetch_related('orderitem_set').order_by('-id')


class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(OrderSerializer(user_orders(request.user), many=True).data)

    def post(self, request):
        data = CreateOrderSerializer(data=request.data)
        data.is_valid(raise_exception=True)

        with transaction.atomic():
            cart_items = list(Cart.objects.filter(user=request.user).select_related('product').order_by('id'))
            if not cart_items:
                raise serializers.ValidationError({'non_field_errors': 'Your cart is empty.'})

            # Lock the products, so two orders at the same time cannot take the same stock
            products = {
                product.id: product
                for product in Product.objects.select_for_update().filter(
                    id__in=[item.product_id for item in cart_items]
                )
            }

            order = Order.objects.create(
                user=request.user,
                phone_number=data.validated_data['phone_number'],
                requires_delivery=data.validated_data['requires_delivery'],
                delivery_address=data.validated_data['delivery_address'] or None,
                payment_on_get=data.validated_data['payment_on_get'],
            )

            for item in cart_items:
                product = products[item.product_id]
                if product.quantity < item.quantity:
                    # Raising inside atomic() cancels everything, including the order
                    raise serializers.ValidationError({
                        'non_field_errors': f'Not enough "{product.name}" in stock. Available: {product.quantity}.'
                    })
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    name=product.name,
                    price=product.sell_price(),
                    quantity=item.quantity,
                )
                product.quantity -= item.quantity
                product.save()

            Cart.objects.filter(user=request.user).delete()

        return Response(OrderSerializer(user_orders(request.user).get(id=order.id)).data, status=201)
