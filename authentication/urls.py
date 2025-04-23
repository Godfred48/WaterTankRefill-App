from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name = 'home'),
    path('signin/', views.signin, name='signin'),
    path('customer_dashboard/', views.customer_dashboard, name='customer_dashboard'),
]