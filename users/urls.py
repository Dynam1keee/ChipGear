from django.urls import path
from users import views

app_name = 'users'

urlpatterns = [
    #localhost/login/
    path('login/', views.login, name='login'),
    #localhost/registration/
    path('registration/', views.registration, name='registration'),
    #localhost/profile/
    path('profile/', views.profile, name='profile'),
    #localhost/users_cart/
    path('users_cart/', views.users_cart, name='users_cart'),
    #localhost/logout/
    path('logout/', views.logout, name='logout'),
]