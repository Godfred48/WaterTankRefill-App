from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin,Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from packages.id_generator import UniqueIDField
from django.utils.timezone import now

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Group, Permission
from django.core.validators import RegexValidator
from django.utils import timezone
from django.contrib.auth.base_user import BaseUserManager
from django.core.exceptions import ValidationError


GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female')]
STATUS_CHOICES = [('A', 'Available'), ('B', 'Busy')]
TANK_STATUS = [('Available', 'Available'), ('Unavailable', 'Unavailable')]
DELIVERY_STATUS = [('Pending', 'Pending'), ('En Route', 'En Route'), ('Delivered', 'Delivered')]
PAYMENT_METHODS = [('Momo On Delivery', 'Momo On Delivery'),  ('Cash On Delivery', 'Cash On Delivery')]
DESCIPLINE_CHOICES = [('Active', 'Active'), ('Suspended', 'Suspended')]
TANK_CHOICES = [('Horizontal Water Tank', 'Horizontal Water Tank'), ('Vertical Water Tank', 'Vertical Water Tank'), ('IBC Water Tank', 'IBC Water Tank')]

VEHICLE_CHOICES = [
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('truck', 'Truck'),
        ('minivan', 'Minivan'),
        ('coupe', 'Coupe'),
        ('convertible', 'Convertible'),
        ('wagon', 'Wagon'),
        ('hatchback', 'Hatchback'),
        ('pickup', 'Pickup'),
        ('motorcycle', 'Motorcycle'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
    ]

TANK_LITRES = [
    ('500L', '500L'),
    ('750L', '750L'),
    ('1000L', '1000L'),
    ('1500L', '1500L'),
    ('2000L', '2000L'),
    ('2500L', '2500L'),
    ('3000L', '3000L'),
]


TANK_SIZES = {  
    '500L': 500,
    '750L': 750,
    '1000L': 1000,
    '1500L': 1500,
    '2000L': 2000,
    '2500L': 2500,
    '3000L': 3000,
}


PAYMENT_STATUS = [('Received', 'Received'),  ('Pending', 'Pending')]

class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, email=None, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("Phone number is required")
        email = self.normalize_email(email)
        user = self.model(phone_number=phone_number, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone_number, email, password, **extra_fields)







class User(AbstractBaseUser, PermissionsMixin):
    user_id = UniqueIDField(primary_key=True, unique=True, editable=False)
    email = models.EmailField(unique=True, blank=True, null=True)
    phone_number = models.CharField(max_length=15, unique=True, validators=[
        RegexValidator(regex=r'^\+?\d{9,15}$', message="Enter a valid phone number.")
    ])
    full_name = models.CharField(max_length=100)
    address = models.CharField(max_length=255, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    photo = models.ImageField(upload_to='uploaded_files/kyc/photos/', default='media/profile.png', null=True, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)

    # Permissions & roles
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=False)
    is_vendor = models.BooleanField(default=False)
    is_driver = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    groups = models.ManyToManyField(Group, related_name="custom_user_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions", blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['email', 'full_name']

    def __str__(self):
        return self.full_name

    def get_full_name(self):
        return f"{self.full_name}"


    def get_photo(self):
        if self.photo:
            return self.photo.url
        else:
            return ""




class Vendor(models.Model):
    vendor_id = UniqueIDField(primary_key=True, editable=False, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="vendor_profile")
    business_name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    price_per_liter = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=DESCIPLINE_CHOICES, default='Active')


    def __str__(self):
        return self.business_name




class Driver(models.Model):
    driver_id = UniqueIDField(primary_key=True, editable=False, unique=True)
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='driver_profile')
    vendor = models.ForeignKey('Vendor', on_delete=models.CASCADE, related_name='drivers')  # 🔥 Linked to Vendor
    license_number = models.CharField(max_length=100, unique=True)
    vehicle_type = models.CharField(max_length=100,choices=VEHICLE_CHOICES,default='sedan')  # You can change this default if you prefer)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='A')  # A = Available, B = Busy
    current_location = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.user.full_name} ({self.vendor.business_name})"





class Tank(models.Model):
    tank_id = UniqueIDField(primary_key=True, editable=False, unique=True)
    photo = models.ImageField(upload_to='uploaded_files/tank/photos/', default='media/tank.png', null=True, blank=True)
    tank_size = models.PositiveIntegerField()
    tank_type = models.CharField(max_length=100, choices=TANK_CHOICES)
    litres = models.CharField(max_length=100, null=True, blank=True,choices=TANK_LITRES)
    availability_status = models.CharField(max_length=20, choices=TANK_STATUS)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="tanks")

    def __str__(self):
        return f"{self.tank_type} - {self.tank_size}L"

    def get_price(self):

        if self.vendor and self.tank_size is not None:  # Check for both
            return self.vendor.price_per_liter * self.tank_size
        else:
            return 0
        

    def save(self, *args, **kwargs):
        if self.litres:
            self.tank_size = TANK_SIZES.get(self.litres, 0)  # Update tank_size
        super().save(*args, **kwargs)


    def clean(self):
        if not self.litres and not self.tank_size:
            raise ValidationError("Either 'litres' or 'tank_size' must be provided.")
        elif self.litres and self.tank_size and TANK_SIZES.get(self.litres) != self.tank_size:
            raise ValidationError(
                f"Tank size {self.tank_size} does not match the size for {self.litres}."
            )




class Order(models.Model):
    order_id = UniqueIDField(primary_key=True, editable=False, unique=True)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders", limit_choices_to={'is_customer': True})
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="orders")
    order_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=100, choices=PAYMENT_METHODS)
    litres = models.CharField(max_length=100, null=True)
    tank_type = models.CharField(max_length=200, choices=TANK_CHOICES)
    status = models.CharField(
        max_length=20, choices=DELIVERY_STATUS, default='Pending'
    )
    is_complete = models.BooleanField(default=False)
    

    def __str__(self):
        return f"Order #{self.order_id} - {self.customer.full_name} - {self.status}"

    def get_total_price(self):
        if self.vendor.price_per_liter:
            return self.vendor.price_per_liter * self.litres
        else:
            return 0


class Payment(models.Model):
    payment_id = UniqueIDField(primary_key=True, editable=False, unique=True)
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name='payment'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHODS)
    payment_status = models.CharField(max_length=45, choices=PAYMENT_STATUS)
    transaction_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Payment #{self.payment_id} - Order #{self.order.order_id} - {self.payment_status}"


class Delivery(models.Model):
    delivery_id = UniqueIDField(primary_key=True, editable=False, unique=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="delivery")
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS)
    delivery_date = models.DateTimeField(default=timezone.now)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    is_deleivered = models.BooleanField(default=False)

    def __str__(self):
        return f"Delivery for Order #{self.order.order_id}"



class Review(models.Model):
    review_id = UniqueIDField(primary_key=True, editable=False, unique=True)
    rating = models.PositiveIntegerField()
    text_review = models.TextField(max_length=500)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_customer': True})
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    review_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.rating} - {self.customer.full_name}"
    
