from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib import auth, messages
from carts.models import Cart
from orders.models import Order, OrderItem
from django.db.models import Prefetch

from users.forms import ProfileForm, UserLoginForm, UserRegistrationForm

def login(request):
    if request.method == 'POST':
        # Передаємо request першим аргументом!
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            # AuthenticationForm сама перевіряє дані та зберігає користувача
            user = form.get_user()
            auth.login(request, user)
            messages.success(request, 'You have logged in')

            session_key = request.session.session_key
            if session_key:
                Cart.objects.filter(session_key=session_key).update(user=user)

            redirect_page = request.POST.get('next', None)
            if redirect_page and redirect_page != reverse('user:logout'):
                return HttpResponseRedirect(redirect_page)

            return HttpResponseRedirect(reverse('main:index'))
        else:
            # Якщо форма не пройшла валідацію, додаємо повідомлення для користувача
            messages.warning(request, 'Wrong username or password')
    else:
        form = UserLoginForm()
        
    context = {
        'title': 'ChipGear - Log in',
        'form': form
    }
    return render(request, 'users/login.html', context)


def registration(request):
    if request.method == 'POST':
        form = UserRegistrationForm(data=request.POST)
        if form.is_valid():
            form.save()

            session_key = request.session.session_key

            user = form.instance
            auth.login(request, user)

            if session_key:
                Cart.objects.filter(session_key=session_key).update(user=user)
            
            messages.success(request, 'You have registered and logged in')
            return HttpResponseRedirect(reverse('main:index'))
    else:
        form = UserRegistrationForm()

    context = {
        'title': 'ChipGear - Registration',
        'form': form
    }
    return render(request, 'users/registration.html', context)

def users_cart(request):
    context = {
        'title': 'My cart - ChipGear',
        'is_cart_page': True,
    }
    return render(request, 'users/users_cart.html', context)

@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(data=request.POST, instance=request.user, files=request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully')
            return HttpResponseRedirect(reverse('user:profile'))
    else:
        form = ProfileForm(instance=request.user)

    orders = (
        Order.objects.filter(user=request.user)
            .prefetch_related(
                Prefetch(
                    'orderitem_set',
                    queryset=OrderItem.objects.select_related('product'),
                )
            )
            .order_by('-id')
    )

    context = {
        'title': 'ChipGear - Profile',
        'is_profile_page': True,
        'form': form,
        'orders': orders
    }
    return render(request, 'users/profile.html', context)

@login_required
def logout(request):
    messages.success(request, 'You have logged out')
    auth.logout(request)
    return redirect(reverse('main:index'))