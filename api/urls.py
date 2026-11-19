from django.urls import path

from api import views

app_name = 'api'

urlpatterns = [
    # localhost/api/categories/
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
]
