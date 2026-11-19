from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from carts.models import Cart
from carts.utils import get_user_carts, parse_positive_int
from goods.models import Product


def _error(message, status=400):
    return JsonResponse({'message': message}, status=status)


def _cart_response(request, **extra):
    """Render the cart fragments that the JavaScript swaps into the page."""
    user_cart = get_user_carts(request)

    response_data = {
        'cart_items_html': render_to_string('carts/cart.html', {'carts': user_cart}, request=request),
        'cart_items_nav_html': render_to_string('base.html', {'carts': user_cart}, request=request),
    }
    response_data.update(extra)

    return JsonResponse(response_data)


@require_POST
def cart_add(request):
    product_id = parse_positive_int(request.POST.get('product_id'))
    if product_id is None:
        return _error('Invalid product')

    product = get_object_or_404(Product, id=product_id)

    # get_user_carts() creates a session for new guests, so session_key is set
    cart = get_user_carts(request).filter(product=product).first()
    new_quantity = cart.quantity + 1 if cart else 1

    if new_quantity > product.quantity:
        return _error('Not enough items in stock')

    if cart:
        cart.quantity = new_quantity
        cart.save()
    elif request.user.is_authenticated:
        Cart.objects.create(user=request.user, product=product, quantity=1)
    else:
        Cart.objects.create(session_key=request.session.session_key, product=product, quantity=1)

    return _cart_response(request)


@require_POST
def cart_change(request):
    cart_id = parse_positive_int(request.POST.get('cart_id'))
    quantity = parse_positive_int(request.POST.get('quantity'))
    if cart_id is None or quantity is None:
        return _error('Invalid cart or quantity')

    # Only carts that belong to the current user/session can be changed
    cart = get_object_or_404(get_user_carts(request), id=cart_id)

    if quantity > cart.product.quantity:
        return _error('Not enough items in stock')

    cart.quantity = quantity
    cart.save()

    return _cart_response(request, message='Quantity changed', quantity=quantity)


@require_POST
def cart_remove(request):
    cart_id = parse_positive_int(request.POST.get('cart_id'))
    if cart_id is None:
        return _error('Invalid cart')

    # Only carts that belong to the current user/session can be removed
    cart = get_object_or_404(get_user_carts(request), id=cart_id)
    quantity = cart.quantity
    cart.delete()

    return _cart_response(request, quantity_deleted=quantity)
