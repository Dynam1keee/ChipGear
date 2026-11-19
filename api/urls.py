from django.urls import path

from api import views

app_name = 'api'

urlpatterns = [
    # localhost/api/categories/
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    # localhost/api/products/
    path('products/', views.ProductListView.as_view(), name='product_list'),
    # localhost/api/products/product_slug/
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
]
