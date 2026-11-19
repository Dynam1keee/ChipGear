from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import redirect
from carts.models import Cart
from orders.forms import CreateOrderForm
from orders.models import Order, OrderItem
from django.db import transaction
from django.forms import ValidationError
from django.contrib.auth.decorators import login_required

@login_required
def create_order(request):
    if request.method == 'POST':
        form = CreateOrderForm(data=request.POST)
        if form.is_valid():
            user = request.user
            cart_items = Cart.objects.filter(user=user).select_related('product')

            # Nothing to order: tell the user instead of showing the form again
            if not cart_items.exists():
                messages.warning(request, 'Your cart is empty')
                return redirect('user:users_cart')

            try:
                with transaction.atomic():
                    # Create order
                    order = Order.objects.create(
                        user = user,
                        phone_number = form.cleaned_data['phone_number'],
                        requires_delivery = form.cleaned_data['requires_delivery'],
                        delivery_address = form.cleaned_data['delivery_address'],
                        payment_on_get = form.cleaned_data['payment_on_get']
                    )
                    # Create ordered items
                    for cart_item in cart_items:
                        product = cart_item.product
                        name = cart_item.product.name
                        price = cart_item.product.sell_price()
                        quantity = cart_item.quantity

                        if product.quantity < quantity:
                            raise ValidationError(f'Insufficient product quantity in stock. Available - {product.quantity}')

                        OrderItem.objects.create(
                            order = order,
                            product = product,
                            name = name,
                            price = price,
                            quantity = quantity
                        )
                        product.quantity -= quantity
                        product.save()

                    # Clear the cart after order creation
                    cart_items.delete()
            except ValidationError as e:
                messages.error(request, ' '.join(e.messages))
                return redirect('orders:create_order')

            messages.success(request, 'Order placed successfully!')
            return redirect('user:profile')
    else:
        initial = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
        }

        form = CreateOrderForm(initial=initial)

    context = {
        'title': 'ChipGear - Order placement',
        'form': form,
        'order': True
    }
    return render(request, 'orders/create_order.html', context=context)
