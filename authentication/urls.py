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
    path('vendor/view_driver/', VendorViewDrivers.as_view(), name='vendor_view_driver'),
    path('vendor/profile/edit/', VendorProfileEditView.as_view(), name='vendor_profile_edit'),
    #vendors
    path('vendor/profile/<str:user_id>/', VendorProfileDetailView.as_view(), name='vendor_profile_detail'),
    path('vendor/profile/', VendorProfileView.as_view(), name='vendor_profile'),
    path('vendor/payments/', PaymentListView.as_view(), name='vendor_payments'),
    
    path('customer/vendors/', Vendors.as_view(), name='vendors'),
    path('vendor/orders/', VendorViewOrders.as_view(), name='vendor_orders'),
    #customer orders
    path('customer/orders/', CustomerViewOrders.as_view(), name='customer_orders'),
    path('customer/deliveries/', CustomerDeliveryListView.as_view(), name='customer_deliveries'),
    path('customer/payments/', CustomerPaymentListView.as_view(), name='customer_payments'),
    path('customer/profile/', CustomerProfileView.as_view(), name='customer_profile'),
    path('customer/profile/update/', CustomerProfileUpdateView.as_view(), name='customer_profile_update'),
    path('profile/<str:user_id>/', CustomerProfileDetailView.as_view(), name='customer_profile_detail'),
    path('delivery-tracking/<str:delivery_id>/', views.test_customer_delivery_tracking, name='customer_delivery_tracking'),
    path('second-delivery-tracking/<str:delivery_id>/', views.test_driver_delivery_tracking, name='driver_delivery_tracking'),
    # driver dashboard
    path('driver_dashboard/', DriverDashboard.as_view(), name='driver_dashboard'),
    path('driver/assigned/', AssignedDeliveriesView.as_view(), name='assigned_deliveries'),
    path('driver/deliveries/<str:delivery_id>/mark_delivered/', views.MarkDeliveryAsDeliveredView.as_view(), name='mark_delivery_delivered'),
    path('driver/profile/', DriverProfileView.as_view(), name='driver_profile'),
    path('driver/history/', DeliveryHistoryView.as_view(), name='delivery_history'),
    path('driver/deliveries/', DriverDeliveryListView.as_view(), name='driver_delivery_list'),
    #delivery urls path
    path('delivery/<str:delivery_id>/status/', views.get_delivery_status, name='get_delivery_status'),
    path('customer/delivery/<str:delivery_id>/track/', views.customer_track_delivery, name='customer_track_delivery'),
    path('driver/delivery/<str:delivery_id>/track/', views.driver_track_delivery, name='driver_track_delivery'),
    path('delivery/', views.track_delivery_view, name = "testing"),

    path('post-location/', views.update_location, name='post_location'),
    path('get-opponent-location/', views.get_opponent_location, name='get_opponent_location'),

]