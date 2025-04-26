from django.urls import path
from . import views
from .views import *

urlpatterns = [
    path('', views.home, name = 'home'),
    path('signin/', views.signin, name='signin'),
    path('customer_dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('about/', views.about, name = 'about'),
    path('services/', views.services, name = 'services'),
    path('signup/', views.signup, name = 'signup'),
    path('orders/', views.orders, name= 'orders'),
    # testing paths
    path('test/signin/', LoginView.as_view(), name= 'test/login'),
    path('test/signup/', SignUpView.as_view(), name= 'test/signup'),
    path('Logout/', LogoutView.as_view(), name = 'logout'),
    path('vendor_dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
    path('vendor/unboard_driver/', DriverOnboardingView.as_view(), name='onboard_drive'),

]