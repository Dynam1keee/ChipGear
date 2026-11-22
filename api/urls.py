from django.urls import path

from api import auth, cart, discovery, orders, pc_builder, views

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
    # localhost/api/builder/ , builder/<slot>/ , builder/<slot>/options/ , builder/add-to-cart/
    path('builder/', pc_builder.BuildView.as_view(), name='builder'),
    path('builder/add-to-cart/', pc_builder.AddBuildToCartView.as_view(), name='builder_add_to_cart'),
    path('builder/<slug:slot>/', pc_builder.BuildSlotView.as_view(), name='builder_slot'),
    path('builder/<slug:slot>/options/', pc_builder.SlotOptionsView.as_view(), name='builder_options'),
    # localhost/api/orders/
    path('orders/', orders.OrderListView.as_view(), name='orders'),
    # localhost/api/filters/
    path('filters/', views.FilterFacetsView.as_view(), name='filters'),
    # localhost/api/products/
    path('products/', views.ProductListView.as_view(), name='product_list'),
    # localhost/api/top-sales/ , recently-viewed/
    path('top-sales/', discovery.TopSalesView.as_view(), name='top_sales'),
    path('recently-viewed/', discovery.RecentlyViewedView.as_view(), name='recently_viewed'),
    # localhost/api/products/product_slug/related/ , view/
    path('products/<slug:slug>/related/', discovery.RelatedProductsView.as_view(), name='product_related'),
    path('products/<slug:slug>/view/', discovery.ViewProductView.as_view(), name='product_view'),
    # localhost/api/products/product_slug/
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
]
