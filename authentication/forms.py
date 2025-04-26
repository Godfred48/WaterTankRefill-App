from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User
from django.contrib.auth import authenticate
from django import forms
from django.contrib.auth import get_user_model
from .models import Driver

User = get_user_model()


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


class SignUpForm(forms.Form):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField()
    phone = forms.CharField(max_length=15)
    address = forms.CharField(max_length=255)
    gender = forms.ChoiceField(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    role = forms.ChoiceField(choices=[('Customer', 'Customer'), ('Vendor', 'Vendor')])
    password = forms.CharField(widget=forms.PasswordInput)
    confirmPassword = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control',
                'required': 'true'
            })

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirmPassword")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data


class LoginForm(forms.Form):
    username = forms.CharField(label="Phone Number or Email")
    password = forms.CharField(widget=forms.PasswordInput)


#driver onboarding form


class DriverOnboardingForm(forms.Form):
    full_name = forms.CharField(max_length=100)
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=15)
    address = forms.CharField(max_length=255)
    gender = forms.ChoiceField(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    license_number = forms.CharField(max_length=100)
    vehicle_type = forms.ChoiceField(choices=VEHICLE_CHOICES)

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']
        if User.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError("A user with this phone number already exists.")
        return phone

    def clean_license_number(self):
        license_number = self.cleaned_data['license_number']
        if Driver.objects.filter(license_number=license_number).exists():
            raise forms.ValidationError("A driver with this license number already exists.")
        return license_number
