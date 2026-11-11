from django.urls import path
from carts import views

app_name = 'carts'

urlpatterns = [
    # localhost/cart/cart_add/
    path('cart_add/', views.cart_add, name='cart_add'),
    # localhost/cart/cart_change/
    path('cart_change/', views.cart_change, name='cart_change'),
    # localhost/cart/cart_remove/
    path('cart_remove/', views.cart_remove, name='cart_remove')
]