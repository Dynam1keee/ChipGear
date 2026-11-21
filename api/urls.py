from django.urls import path

from api import auth, cart, orders, views

app_name = 'api'

urlpatterns = [
    # localhost/api/categories/
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    # localhost/api/auth/csrf/ , me/ , login/ , register/ , logout/
    path('auth/csrf/', auth.CsrfView.as_view(), name='csrf'),
    path('auth/me/', auth.MeView.as_view(), name='me'),
    path('auth/login/', auth.LoginView.as_view(), name='login'),
    path('auth/register/', auth.RegisterView.as_view(), name='register'),
    path('auth/logout/', auth.LogoutView.as_view(), name='logout'),
    # localhost/api/cart/
    path('cart/', cart.CartView.as_view(), name='cart'),
    # localhost/api/cart/items/
    path('cart/items/', cart.CartItemListView.as_view(), name='cart_items'),
    # localhost/api/cart/items/cart_item_id/
    path('cart/items/<int:item_id>/', cart.CartItemDetailView.as_view(), name='cart_item'),
    # localhost/api/orders/
    path('orders/', orders.OrderListView.as_view(), name='orders'),
    # localhost/api/filters/
    path('filters/', views.FilterFacetsView.as_view(), name='filters'),
    # localhost/api/products/
    path('products/', views.ProductListView.as_view(), name='product_list'),
    # localhost/api/products/product_slug/
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
]
