from django.urls import path
from . import views
from .views import *

urlpatterns = [
    path('', HomeView.as_view(), name = 'home'),
    
    path('customer_dashboard/', CustomerDashboard.as_view(), name='customer_dashboard'),
    path('about/', views.about, name = 'about'),
    path('services/', views.services, name = 'services'),
    path('orders/', views.orders, name= 'orders'),
    # testing paths
    path('signin/', LoginView.as_view(), name= 'login'),
    path('signup/', SignUpView.as_view(), name= 'signup'),
    path('Logout/', LogoutView.as_view(), name = 'logout'),
    path('vendor_dashboard/', VendorDashboard.as_view(), name='vendor_dashboard'),
    path('vendor/unboard_driver/', DriverOnboardingView.as_view(), name='onboard_driver'),
    #vendors
    path('customer/vendors/', Vendors.as_view(), name='vendors'),
    path('vendor/orders/', VendorViewOrders.as_view(), name='vendor_orders'),
    #customer orders
    path('customer/orders/', CustomerViewOrders.as_view(), name='customer_orders'),
    # driver dashboard
    path('driver_dashboard/', DriverDashboard.as_view(), name='driver_dashboard'),
    path('driver/assigned/', AssignedDeliveriesView.as_view(), name='assigned_deliveries'),
    path('driver/profile/', DriverProfileView.as_view(), name='driver_profile'),
    path('driver/history/', DeliveryHistoryView.as_view(), name='delivery_history'),

]