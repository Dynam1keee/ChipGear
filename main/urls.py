from django.urls import path
from main import views

app_name = 'main'

urlpatterns = [
    #localhost/
    path('', views.index, name='index'),
    #localhost/about/
    # ! path('about/', views.about, name='about'), check about.html page
]