from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User
from django.contrib.auth import authenticate
from django import forms
from django.contrib.auth import get_user_model
from .models import Driver,Order,Vendor 

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





class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'customer',
            'vendor',
            'payment_method',
            'litres',
            'tank_type',
        ]
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'tank_type': forms.Select(attrs={'class': 'form-control'}),
            'litres': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter number of litres'}),
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'vendor': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_litres(self):
        litres = self.cleaned_data.get('litres')
        if not litres:
            raise forms.ValidationError("This field is required.")
        try:
            litres_value = float(litres)
            if litres_value <= 0:
                raise forms.ValidationError("Litres must be a positive number.")
        except ValueError:
            raise forms.ValidationError("Please enter a valid number for litres.")
        return litres




class VendorProfileForm(forms.ModelForm):
    full_name = forms.CharField(max_length=100, label='Contact Name')
    email = forms.EmailField(required=False)
    address = forms.CharField(max_length=255, required=False, widget=forms.Textarea(attrs={'rows': 2}))

    class Meta:
        model = Vendor
        fields = ['business_name', 'location', 'price_per_liter', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'instance' in kwargs and kwargs['instance']:
            self.fields['full_name'].initial = kwargs['instance'].user.full_name
            self.fields['email'].initial = kwargs['instance'].user.email
            self.fields['address'].initial = kwargs['instance'].user.address

    def save(self, commit=True):
        vendor = super().save(commit=False)
        vendor.user.full_name = self.cleaned_data['full_name']
        vendor.user.email = self.cleaned_data['email']
        vendor.user.address = self.cleaned_data['address']
        vendor.user.save()
        if commit:
            vendor.save()
        return vendor