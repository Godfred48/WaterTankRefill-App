from django.shortcuts import render,redirect
from packages.log_entry import create_log_entry
from django.views.generic import FormView, RedirectView
from django.contrib.auth import login, authenticate, logout
from django.urls import reverse_lazy
from .forms import SignUpForm, LoginForm,DriverOnboardingForm
from .models import User
from .models import *
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.views.generic import View,CreateView,UpdateView,DeleteView,DetailView,ListView
from django.contrib.auth import get_user_model
from .forms import *
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from packages.decorators import vendor_required, customer_required, admin_required
from django.utils.decorators import method_decorator
from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncYear
import json
from django.shortcuts import get_object_or_404


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
    return render(request, 'customer/order_form.html')

def vendor_dashboard(request):
    return render(request, 'vendor/vendor_dashboard.html')




import secrets
import string

# Generate a secure random password
def generate_random_password(length=10):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


class HomeView(View):
    template_name = 'home.html'
    def get(self, request):
        
        return render(self.request, self.template_name)




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
        return redirect('login')



User = get_user_model()
@method_decorator((login_required, vendor_required), name='dispatch')
class DriverOnboardingView(FormView):
    template_name = 'vendor/driver_onboard.html'
    form_class = DriverOnboardingForm
    success_url = reverse_lazy('vendor_dashboard')

    def form_valid(self, form):
        user = self.request.user
        if not user.is_vendor:
            messages.error(self.request, "Only vendors can onboard drivers.")
            return redirect('home')
        # Generate and set a random password
        random_password = generate_random_password()


        # Create user account for the driver
        driver_user = User.objects.create_user(
            full_name=form.cleaned_data['full_name'],
            email=form.cleaned_data['email'],
            phone_number=form.cleaned_data['phone_number'],
            address=form.cleaned_data['address'],
            gender=form.cleaned_data['gender'],
            is_driver=True
        )

        driver_user.set_password(random_password)
        driver_user.save()
        vendor = Vendor.objects.get(user=user)

        # Link driver profile
        Driver.objects.create(
            user=driver_user,
            vendor=vendor,  # assuming there's a related_name from User to Vendor
            license_number=form.cleaned_data['license_number'],
            vehicle_type=form.cleaned_data['vehicle_type']
        )
        

        messages.success(self.request, "Driver onboarded successfully.")
        return super().form_valid(form)


@method_decorator((login_required, customer_required), name='dispatch')
class Vendors(View):
    
    template_name = 'customer/test/order_form.html'

    def get(self,request,*args,**kwargs):
        query = request.GET.get('q')  # <-- get search query from URL
        if query:
            vendors = Vendor.objects.filter(
                Q(name__icontains=query) |
                Q(location__icontains=query) |
                Q(phone__icontains=query)
            )
        else:
           vendors = Vendor.objects.all()
        #vendors = Vendor.objects.all()
        form = OrderForm()
        context = {'vendors': vendors, 'form': form}
        return render(request, self.template_name,context)
        

    def post(self, request, *args, **kwargs):
        vendor_id = request.POST.get('vendor_id')
        delivery_location = request.POST.get('delivery_location')
        liters = request.POST.get('liters')
        total_price = request.POST.get('total_price')
        payment_method = request.POST.get('payment_method')
        tank_type = request.POST.get('tank_choices')

        vendor = Vendor.objects.get(pk=vendor_id)

        order = Order.objects.create(
        customer=request.user,
        vendor=vendor,
        delivery_location=delivery_location,
        litres=liters,
        payment_method=payment_method,
        tank_type=tank_type
      )
        payment = Payment.objects.create(
        order=order,amount=order.get_total_price(),payment_method=order.payment_method,payment_status=order.status,transaction_id="Cash"
       )
        delivery = Delivery.objects.create(order=order, payment=payment,is_deleivered=False,delivery_status="Pending")

        messages.success(request, 'Your order has been placed successfully!')
        return redirect('customer_dashboard')



@method_decorator((login_required, customer_required), name='dispatch')
class CustomerDashboard(View):
    template_name = 'customer/customer_dashboard.html'
    def get(self, request,*args,**kwargs):
        orders = Order.objects.filter(customer=request.user).order_by('-order_date')
        completed_orders = orders.filter(is_complete=True)
        pending_orders = orders.filter(is_complete=False)
        active_refills = orders.filter(status='Delivered') 

        context = {
            'orders': orders,
            'completed_orders_count': completed_orders.count(),
            'pending_orders_count': pending_orders.count(),
            'active_refills_count': active_refills.count(),
        }
        return render(request, self.template_name,context)



@method_decorator((login_required, customer_required), name='dispatch')
class CustomerViewOrders(ListView):
    model = Order
    template_name = 'customer/orders.html'
    context_object_name = 'orders'

    def get_queryset(self):
        # Only fetch orders related to the logged-in customer
        return Order.objects.filter(customer=self.request.user).order_by('-order_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orders = Order.objects.filter(customer=self.request.user).order_by('-order_date')
        completed_orders = orders.filter(is_complete=True)
        pending_orders = orders.filter(is_complete=False)
        active_refills = orders.filter(status='Delivered') 
         # Monthly order analysis
        monthly_orders = (
            orders.annotate(month=TruncMonth('order_date'))
                  .values('month')
                  .annotate(count=Count('order_id'))
                  .order_by('month')
        )
        monthly_data = {
            item['month'].strftime('%b %Y'): item['count']
            for item in monthly_orders
        }

        # Yearly order analysis
        yearly_orders = (
            orders.annotate(year=TruncYear('order_date'))
                  .values('year')
                  .annotate(count=Count('order_id'))
                  .order_by('year')
        )
        yearly_data = {
            item['year'].year: item['count']
            for item in yearly_orders
        }

        # Last Delivery (most recent delivered order)
        last_delivery = active_refills.order_by('-order_date').first()
        context.update({
            'page_name': 'order_list',
            'list_name': 'order_list',
            'completed_orders': completed_orders,
            'pending_orders': pending_orders,
            'active_refills': active_refills,
            'total_orders': orders.count(),
            'monthly_orders': monthly_orders,
            'yearly_orders': yearly_orders,
            'last_delivery': last_delivery,
        })
        context['monthly_data_json'] = json.dumps(monthly_data)
        context['yearly_data_json'] = json.dumps(yearly_data)
        return context





@method_decorator((login_required, vendor_required), name='dispatch')
class VendorViewOrders(ListView):
    model = Order
    template_name = 'vendor/new_order.html'
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(vendor=self.request.user.vendor_profile).order_by('-order_date')

    def post(self, request, *args, **kwargs):
        order_id = request.POST.get('order_id')
        driver_id = request.POST.get('driver_id')
        order = get_object_or_404(Order, order_id=order_id, vendor=request.user.vendor_profile)

        # Update order status to accepted
        order.status = 'Accepted'
        messages.success(request, f"Order status updated successfully")
        order.save()
        # Assign driver and create delivery entry
        if driver_id:
            from .models import Driver, Delivery,Payment
            driver = get_object_or_404(Driver, driver_id=driver_id, vendor=request.user.vendor_profile)
            driver.status = 'A'
            driver.save()
            delivery = Delivery.objects.get(order=order)
            delivery.delivery_status = "In Progress"
            delivery.driver = driver
            delivery.save()
        return redirect('vendor_orders')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orders = Order.objects.filter(vendor=self.request.user.vendor_profile).order_by('-order_date')
        completed_orders = orders.filter(is_complete=True)
        pending_orders = orders.filter(is_complete=False)
        active_refills = orders.filter(status='Delivered') 
         # Monthly order analysis
        monthly_orders = (
            orders.annotate(month=TruncMonth('order_date'))
                  .values('month')
                  .annotate(count=Count('order_id'))
                  .order_by('month')
        )
        monthly_data = {
            item['month'].strftime('%b %Y'): item['count']
            for item in monthly_orders
        }

        # Yearly order analysis
        yearly_orders = (
            orders.annotate(year=TruncYear('order_date'))
                  .values('year')
                  .annotate(count=Count('order_id'))
                  .order_by('year')
        )
        yearly_data = {
            item['year'].year: item['count']
            for item in yearly_orders
        }

        # Last Delivery (most recent delivered order)
        last_delivery = active_refills.order_by('-order_date').first()
        context.update({
            'page_name': 'order_list',
            'list_name': 'order_list',
            'completed_orders': completed_orders,
            'pending_orders': pending_orders,
            'active_refills': active_refills,
            'total_orders': orders.count(),
            'monthly_orders': monthly_orders,
            'yearly_orders': yearly_orders,
            'last_delivery': last_delivery,
            'available_drivers': self.request.user.vendor_profile.drivers.filter(status='A'),
        })
        context['monthly_data_json'] = json.dumps(monthly_data)
        context['yearly_data_json'] = json.dumps(yearly_data)
        return context


@method_decorator((login_required, vendor_required), name='dispatch')
class VendorDashboard(View):
    template_name = 'vendor/vendor_dashboard.html'
    def get(self, request, *args, **kwargs):
        
        vendor = request.user.vendor_profile
        orders = Order.objects.filter(vendor=vendor).order_by('-order_date')
        completed_orders = orders.filter(is_complete=True)
        pending_orders = orders.filter(is_complete=False)
        active_refills = orders.filter(status='Delivered') 

        # Monthly order analysis
        monthly_orders = (
            orders.annotate(month=TruncMonth('order_date'))
                  .values('month')
                  .annotate(count=Count('order_id'))
                  .order_by('month')
        )
        monthly_data = {
            item['month'].strftime('%b %Y'): item['count']
            for item in monthly_orders
        }

        context = {
            'orders': orders[:5],  # recent 5 orders
            'completed_orders_count': completed_orders.count(),
            'pending_orders_count': pending_orders.count(),
            'active_refills_count': active_refills.count(),
            'monthly_data_json': json.dumps(monthly_data),
            
        }
        return render(request, self.template_name, context)
