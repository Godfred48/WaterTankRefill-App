from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User,Vendor,Driver,Tank,Order,Payment,Delivery,Review

from django.contrib.admin.models import LogEntry
from django.utils.html import format_html


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ['-date_joined']
    list_display = [
        'phone_number', 'email', 'full_name', 'is_active',
        'is_customer', 'is_vendor', 'is_driver', 'is_admin',
        'latitude', 'longitude', 'photo_tag'
    ]
    list_filter = [
        'is_customer', 'is_vendor', 'is_driver', 'is_admin',
        'is_active', 'gender'
    ]
    search_fields = ['phone_number', 'email', 'full_name']

    readonly_fields = ['user_id', 'date_joined', 'photo_preview']

    fieldsets = (
        (_('Personal Info'), {
            'fields': (
                'user_id', 'phone_number', 'email', 'full_name', 'address',
                'gender', 'photo_preview', 'latitude', 'longitude', 'date_joined'
            )
        }),
        (_('Roles & Permissions'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'is_customer', 'is_vendor', 'is_driver', 'is_admin',
                'groups', 'user_permissions'
            )
        }),
        (_('Security'), {
            'fields': ('password',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'email', 'full_name', 'password1', 'password2'),
        }),
    )

    def photo_tag(self, obj):
        if obj.photo:
            return format_html('<img src="{}" style="width: 40px; height: 40px; border-radius: 50%;" />', obj.photo.url)
        return "-"
    photo_tag.short_description = 'Photo'

    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" style="width: 100px; height: 100px; border-radius: 8px;" />', obj.photo.url)
        return "No Photo"
    photo_preview.short_description = 'Current Photo'

    


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'location', 'price_per_liter', 'user']
    search_fields = ['business_name', 'user__full_name', 'location']
    list_filter = ['location']



@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('user', 'vendor', 'license_number', 'vehicle_type', 'status', 'current_location')
    search_fields = ('user__full_name', 'vendor__business_name', 'license_number')
    list_filter = ('status', 'vehicle_type', 'vendor')



@admin.register(Tank)
class TankAdmin(admin.ModelAdmin):
    list_display = ['tank_id', 'tank_type', 'tank_size', 'availability_status', 'vendor', 'get_price']
    list_filter = ['vendor', 'availability_status', 'tank_type']
    search_fields = ['tank_id', 'tank_type', 'vendor__business_name']
    readonly_fields = ['get_price']

    fieldsets = (
        ('Tank Information', {
            'fields': ('photo', 'tank_size', 'tank_type', 'litres', 'availability_status', 'vendor')  # Removed 'tank_id'
        }),
        ('Price Information', {
            'fields': ('get_price',)
        }),
    )


class OrderAdmin(admin.ModelAdmin):
    # Configuration for the Order model in the admin interface
    list_display = ['order_id', 'customer', 'vendor', 'order_date', 'status'] #added total_amount
    search_fields = ['order_id', 'customer__full_name', 'vendor__business_name', 'status']
    list_filter = ['customer', 'vendor', 'order_date', 'status']
    

class PaymentAdmin(admin.ModelAdmin):
    # Configuration for the Payment model in the admin interface
    list_display = ['payment_id', 'order', 'amount', 'payment_method', 'payment_status', 'transaction_id']
    search_fields = ['payment_id', 'order__order_id', 'payment_method', 'payment_status', 'transaction_id']
    list_filter = ['payment_method', 'payment_status']
    

class DeliveryAdmin(admin.ModelAdmin):
    # Configuration for the Delivery model in the admin interface
    list_display = ['delivery_id', 'order', 'driver', 'delivery_date', 'delivery_status']
    search_fields = ['delivery_id', 'order__order_id', 'driver__user__full_name', 'delivery_status']
    list_filter = ['delivery_status', 'delivery_date', 'driver']
    

class ReviewAdmin(admin.ModelAdmin):
    # Configuration for the Review model in the admin interface
    list_display = ['review_id', 'customer', 'vendor', 'rating', 'review_date']
    search_fields = ['review_id', 'customer__full_name', 'vendor__business_name']
    list_filter = ['vendor', 'review_date']



# Register your models here.  This is what makes them show up in the admin interface.

admin.site.register(Order, OrderAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Delivery, DeliveryAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(LogEntry)
