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
