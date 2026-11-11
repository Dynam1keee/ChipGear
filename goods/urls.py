from django.urls import path
from goods import views

app_name = 'goods'

urlpatterns = [
    #localhost/catalog/search/
    path('search/', views.catalog, name='search'),
    #localhost/catalog/category_slug/search/
    path('<slug:category_slug>/search/', views.catalog, name='search_in_category'),

    #localhost/catalog/category_slug/
    path('<slug:category_slug>/', views.catalog, name='goods_list'),
    #localhost/catalog/category_slug/product_slug/
    path('<slug:category_slug>/<slug:product_slug>/', views.product, name='product'),
]