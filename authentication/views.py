from django.shortcuts import render,redirect
from packages.log_entry import create_log_entry
from django.views.generic import FormView, RedirectView
from django.contrib.auth import login, authenticate, logout
from django.urls import reverse_lazy
from .forms import SignUpForm, LoginForm
from .models import User
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.views.generic import View,CreateView,UpdateView,DeleteView,DetailView

# Create your views here.
def home(request):
    return render(request, 'home.html')


def signin(request):
    return render(request, 'signin.html')

def customer_dashboard(request):
    return render(request, 'customer/customer_dashboard.html')

def about(request):
    return render(request, 'about.html')

def services(request):
    return render(request, 'services.html')

def signup(request):
    return render(request, 'signup.html')

def orders(request):
    return render(request, 'orders.html')

def vendor_dashboard(request):
    return render(request, 'vendor/vendor_dashboard.html')





class SignUpView(FormView):
    template_name = 'test/signup.html'
    form_class = SignUpForm
    success_url = reverse_lazy('test/login')

    def form_valid(self, form):
        data = form.cleaned_data
        full_name = f"{data['first_name']} {data['last_name']}"
        role = data['role'].lower()

        user = User.objects.create_user(
            full_name=full_name,
            email=data['email'],
            phone_number=data['phone'],
            address=data['address'],
            gender=data['gender'],
            password=data['password']
        )

        # Set role flags
        if role == 'customer':
            user.is_customer = True
        elif role == 'vendor':
            user.is_vendor = True
        user.save()

        # Log the action
        create_log_entry(
            user=user,
            content_type=ContentType.objects.get_for_model(User),
            object_id=user.pk,
            object_repr=str(user),
            action_flag=1,
            change_message=f"User {user.full_name} registered successfully as a {role}"
        )

        messages.success(self.request, "Account created successfully. Please sign in.")
        return super().form_valid(form)


class LoginView(FormView):
    template_name = 'test/signin.html'
    form_class = LoginForm

    def get_success_url(self):
        user = self.request.user
        if user.is_admin:
            return reverse_lazy('customer_dashboard')
        elif user.is_vendor:
            return reverse_lazy('vendor_dashboard')
        elif user.is_customer:
            return reverse_lazy('customer_dashboard')
        elif user.is_driver:
            return reverse_lazy('driver_dashboard')
        return reverse_lazy('home')  # fallback
    

    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(self.request, username=username, password=password)

        if user is not None:
            login(self.request, user)
            messages.success(self.request, f"You have logged in successfully")
            create_log_entry(
                user=user,
                content_type=ContentType.objects.get_for_model(User),
                object_id=user.pk,
                object_repr=str(user),
                action_flag=2,
                change_message= f"User {user.full_name} has logged in successfully"
            )
            return redirect(self.get_success_url())
        else:
            form.add_error(None, "Invalid credentials")
            return self.form_invalid(form)

    


class LogoutView(View):
    def get(self, request):
        if request.user.is_authenticated:
            # Log the logout action
            create_log_entry(
                user=request.user,
                content_type=ContentType.objects.get_for_model(User),
                object_id=request.user.pk,
                object_repr=str(request.user),
                action_flag=2,  # CHANGE action
                change_message=f"User {request.user.full_name} has logged out successfully"
            )

        
        logout(request)
        messages.info(request, 'You have successfully logged out.')
        return redirect('test/login')

