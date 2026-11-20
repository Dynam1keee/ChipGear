from carts.models import Cart


def ensure_session_key(request):
    """Return the session key, creating a session first if the guest has none."""
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def get_user_carts(request):
    if request.user.is_authenticated:
        return Cart.objects.filter(user=request.user).select_related('product')

    return Cart.objects.filter(session_key=ensure_session_key(request)).select_related('product')


def parse_positive_int(value):
    """Convert request data to an int greater than zero, or return None."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None

    return number if number > 0 else None


def merge_guest_cart(session_key, user):
    """
    Move the items of a guest cart (found by its session key) to the user.
    If the user already has the same product, the quantities are added, but
    never above the stock.
    """
    if not session_key:
        return

    guest_items = Cart.objects.filter(
        session_key=session_key, user__isnull=True
    ).select_related('product')

    for guest_item in guest_items:
        user_item = Cart.objects.filter(user=user, product=guest_item.product).first()

        if user_item is None:
            guest_item.user = user
            guest_item.session_key = None
            guest_item.save()
            continue

        wanted = user_item.quantity + guest_item.quantity
        # max(): never make the quantity of the user's own item smaller
        user_item.quantity = max(user_item.quantity, min(wanted, guest_item.product.quantity))
        user_item.save()
        guest_item.delete()
