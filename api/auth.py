"""
Login, registration and logout for the React frontend.

The frontend uses the same cookie session as the Django site. These steps are needed:
1. GET /api/auth/csrf/ once, to get the "csrftoken" cookie.
2. Send its value in the "X-CSRFToken" header with every POST, PATCH and DELETE.
"""
from django.contrib import auth
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import UserSerializer
from carts.utils import merge_guest_cart
from users.forms import ProfileForm, UserLoginForm, UserRegistrationForm


def form_errors(form):
    """{"field": ["message", ...]}; the errors of the whole form are under "non_field_errors"."""
    return {
        ('non_field_errors' if field == '__all__' else field): [str(error) for error in errors]
        for field, errors in form.errors.items()
    }


@method_decorator(csrf_protect, name='dispatch')
class CsrfProtectedView(APIView):
    """
    Django REST Framework checks CSRF only for logged in users. These views
    change the session, so they check it for guests too (against "login CSRF").
    """


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CsrfView(APIView):
    """GET /api/auth/csrf/ - sets the "csrftoken" cookie."""

    def get(self, request):
        return Response({'detail': 'CSRF cookie set.'})


class MeView(APIView):
    """GET /api/auth/me/ - the logged in user, or {"user": null} for a guest."""

    def get(self, request):
        user = UserSerializer(request.user).data if request.user.is_authenticated else None
        return Response({'user': user})

    def patch(self, request):
        """PATCH /api/auth/me/ {"first_name": ..., "last_name": ..., "username": ..., "email": ...}"""
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication credentials were not provided.'}, status=403)

        # Only these fields can be changed here; the avatar is not sent as JSON
        data = {
            field: request.data.get(field, getattr(request.user, field))
            for field in ('first_name', 'last_name', 'username', 'email')
        }
        form = ProfileForm(data=data, instance=request.user)
        if not form.is_valid():
            return Response(form_errors(form), status=400)

        user = form.save()
        return Response({'user': UserSerializer(user).data})


class LoginView(CsrfProtectedView):
    """POST /api/auth/login/ {"username": "...", "password": "..."}"""

    def post(self, request):
        django_request = request._request  # the plain Django request, as auth functions expect
        form = UserLoginForm(django_request, data=request.data)
        if not form.is_valid():
            return Response(form_errors(form), status=400)

        user = form.get_user()
        # Read the guest session key BEFORE login: login() creates a new session key
        guest_session_key = django_request.session.session_key
        auth.login(django_request, user)
        merge_guest_cart(guest_session_key, user)

        return Response({'user': UserSerializer(user).data})


class RegisterView(CsrfProtectedView):
    """POST /api/auth/register/ - creates the user and logs them in."""

    def post(self, request):
        django_request = request._request
        form = UserRegistrationForm(data=request.data)
        if not form.is_valid():
            return Response(form_errors(form), status=400)

        guest_session_key = django_request.session.session_key
        user = form.save()
        auth.login(django_request, user)
        merge_guest_cart(guest_session_key, user)

        return Response({'user': UserSerializer(user).data}, status=201)


class LogoutView(CsrfProtectedView):
    """POST /api/auth/logout/"""

    def post(self, request):
        auth.logout(request._request)
        return Response(status=204)
