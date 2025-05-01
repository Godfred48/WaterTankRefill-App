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
from packages.decorators import vendor_required, customer_required, admin_required, driver_required
from django.utils.decorators import method_decorator
from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncYear
import json
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth, TruncWeek, TruncYear
from django.core.serializers import serialize
import json
from django.views.decorators.csrf import csrf_exempt



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
        # Create user account for the driver
        driver_user = User.objects.create_user(
      full_name=form.cleaned_data['full_name'],
      email=form.cleaned_data['email'],
      phone_number=form.cleaned_data['phone_number'],
      address=form.cleaned_data['address'],
      gender=form.cleaned_data['gender'],
      is_driver=True,
      password=form.cleaned_data['password']  # Use vendor-set password
     )
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




@method_decorator((login_required, driver_required), name='dispatch')
class DriverDashboard(View):
    template_name = 'driver/driver_dashboard.html'

    def get(self, request, *args, **kwargs):
        driver = request.user.driver_profile
        deliveries = Delivery.objects.filter(driver=driver).select_related('order', 'order__customer').order_by('-delivery_date')

        completed_deliveries = deliveries.filter(is_deleivered=True)
        pending_deliveries = deliveries.filter(is_deleivered=False)

        # Monthly delivery analysis
        monthly_deliveries = (
            deliveries.annotate(month=TruncMonth('delivery_date'))
                      .values('month')
                      .annotate(count=Count('delivery_id'))
                      .order_by('month')
        )

        monthly_data = {
            item['month'].strftime('%b %Y'): item['count']
            for item in monthly_deliveries
        }

        # Optional alert logic: count of pending deliveries that are overdue or flagged
        alerts_count = pending_deliveries.filter(delivery_date__lt=timezone.now()).count()

        context = {
            'total_deliveries': deliveries.count(),
            'completed_deliveries': completed_deliveries.count(),
            'pending_deliveries': pending_deliveries.count(),
            'alerts_count': alerts_count,
            'monthly_data_json': json.dumps(monthly_data),
            'deliveries': deliveries[:5],
        }
        return render(request, self.template_name, context)




@method_decorator((login_required, driver_required), name='dispatch')
class DriverProfileView(TemplateView):
    template_name = 'driver/driver_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['driver'] = self.request.user.driver_profile
        return context



@method_decorator((login_required, driver_required), name='dispatch')
class AssignedDeliveriesView(ListView):
    model = Delivery
    template_name = 'driver/assigned_deliveries.html'
    context_object_name = 'deliveries'

    def get_queryset(self):
        driver = self.request.user.driver_profile
        return Delivery.objects.filter(driver=driver, is_deleivered=False).select_related('order').order_by('-delivery_date')



@method_decorator((login_required, driver_required), name='dispatch')
class DeliveryHistoryView(ListView):
    model = Delivery
    template_name = 'driver/delivery_history.html'
    context_object_name = 'deliveries'
    paginate_by = 10  # Optional

    def get_queryset(self):
        driver = self.request.user.driver_profile
        return Delivery.objects.filter(driver=driver, is_deleivered=True).select_related('order').order_by('-delivery_date')



@method_decorator((login_required, driver_required), name='dispatch')
class MarkDeliveryAsDeliveredView(View):
    def post(self, request, delivery_id):
        try:
            delivery = get_object_or_404(Delivery, delivery_id=delivery_id, driver=request.user.driver_profile, is_deleivered=False)
            delivery.is_deleivered = True
            delivery.delivery_status = 'Delivered' 
            delivery.save()
            # Updating the associated order status
            order = delivery.order
            order.status = 'Delivered'
            order.is_complete = True 
            order.save()
            return JsonResponse({'status': 'success', 'message': 'Delivery status updated successfully.'})
        except Delivery.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid delivery ID or delivery already marked as delivered.'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'An error occurred: {str(e)}'}, status=500)



@method_decorator((login_required, customer_required), name='dispatch')
class CustomerProfileView(LoginRequiredMixin,TemplateView):
    template_name = 'customer/customer_profile.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customer'] = self.request.user
        return context



@method_decorator((login_required, customer_required), name='dispatch')
class CustomerProfileUpdateView(LoginRequiredMixin,UpdateView):
    model = User
    template_name = 'customer/customer_profile_update.html'
    fields = ['full_name', 'email', 'address', 'gender', 'photo']
    success_url = reverse_lazy('customer_profile')

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_name'] = 'customer_profile'
        context['list_name'] = 'customers'
        return context



@method_decorator((login_required, customer_required), name='dispatch')
class CustomerProfileDetailView(LoginRequiredMixin,DetailView):
    model = User
    template_name = 'customer/customer_detail.html'
    context_object_name = 'customer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.request.user
        orders = customer.orders.select_related('vendor').all()
        payments = Payment.objects.filter(order__customer=customer).select_related('order')
        total_payments_made = payments.aggregate(total_balance=Sum('amount'))['total_balance'] or 0.00
        deliveries = Delivery.objects.filter(order__in=orders).select_related('order', 'driver')
        reviews = Review.objects.filter(customer=customer).select_related('vendor')

        total_orders = orders.count()
        completed_orders = orders.filter(is_complete=True).count()
        pending_orders = orders.filter(status='Pending').count()
        total_payments = payments.count()
        total_reviews = reviews.count()
        total_spent = total_payments_made
        context.update({
            'page_name': 'customer_profile',
            'list_name': 'customers',
            'orders': orders,
            'payments': payments,
            'deliveries': deliveries,
            'total_payments_made': total_payments_made,
            'reviews': reviews,
            'analytics': {
                'total_orders': total_orders,
                'completed_orders': completed_orders,
                'pending_orders': pending_orders,
                'total_payments': total_payments,
                'total_reviews': total_reviews,
                      }
        })
        return context

    def get_queryset(self):
        return User.objects.filter(is_customer=True)

    def get_object(self):
        return get_object_or_404(User, pk=self.kwargs['user_id'])




@method_decorator((login_required,vendor_required), name='dispatch')
class VendorProfileDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'vendor/vendor_detail.html'
    context_object_name = 'vendor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor_user = self.request.user
        vendor = vendor_user.vendor_profile  # via OneToOneField

        orders = vendor.orders.select_related('customer').all()
        payments = Payment.objects.filter(order__vendor=vendor).select_related('order')
        deliveries = Delivery.objects.filter(order__vendor=vendor).select_related('order', 'driver')
        drivers = Driver.objects.filter(vendor=vendor)
        tanks = vendor.tanks.all()
        reviews = Review.objects.filter(vendor=vendor).select_related('customer')

        total_orders = orders.count()
        completed_orders = orders.filter(is_complete=True).count()
        pending_orders = orders.filter(status='Pending').count()
        total_earnings = payments.aggregate(total=Sum('amount'))['total'] or 0.00
        total_reviews = reviews.count()

        context.update({
            'vendor': vendor,
            'orders': orders,
            'payments': payments,
            'deliveries': deliveries,
            'drivers': drivers,
            'tanks': tanks,
            'reviews': reviews,
            'analytics': {
                'total_orders': total_orders,
                'completed_orders': completed_orders,
                'pending_orders': pending_orders,
                'total_earnings': total_earnings,
                'total_reviews': total_reviews,
                'total_drivers': drivers.count(),
                'total_tanks': tanks.count(),
            }
        })
        return context

    def get_queryset(self):
        return User.objects.filter(is_vendor=True)

    def get_object(self):
        return get_object_or_404(User, pk=self.kwargs['user_id'])



@method_decorator((login_required, vendor_required), name='dispatch')
class VendorViewDrivers(View):
    template_name = 'vendor/vendor_drivers.html'
    context_object_name = 'drivers'

    def get(self, request):
        try:
            vendor = request.user.vendor_profile
            drivers = Driver.objects.filter(vendor=vendor).select_related('user')

            # Get delivery counts for the current month for each driver
            today = timezone.now()
            start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_of_month = (start_of_month.replace(month=start_of_month.month + 1) - timezone.timedelta(days=1)) if start_of_month.month < 12 else today.replace(year=today.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0) - timezone.timedelta(days=1)

            driver_delivery_counts = Delivery.objects.filter(
                driver__vendor=vendor,
                is_deleivered=True,
                delivery_date__gte=start_of_month,
                delivery_date__lte=end_of_month
            ).values('driver').annotate(completed_deliveries=Count('driver')).order_by('driver')

            # Create a dictionary to easily access delivery counts per driver
            driver_delivery_map = {item['driver']: item['completed_deliveries'] for item in driver_delivery_counts}

            # Enhance the driver objects with their delivery counts and progress percentage
            enhanced_drivers = []
            max_deliveries = 10  # Define your maximum for the progress bar
            for driver in drivers:
                completed_count = driver_delivery_map.get(driver.driver_id, 0)
                progress_percentage = (completed_count * 100) / max_deliveries if max_deliveries > 0 else 0
                enhanced_drivers.append({
                    'driver': driver,
                    'completed_deliveries': completed_count,
                    'progress_percentage': progress_percentage
                })

            context = {
                self.context_object_name: enhanced_drivers,
                'vendor': vendor,
                'page_name': 'vendor_drivers',
                'list_name': 'drivers',
                'max_deliveries': max_deliveries,  # Optional: Pass max deliveries to the template
            }
            return render(request, self.template_name, context)
        except Vendor.DoesNotExist:
            messages.info(request, "Vendor does not exist.")
            return redirect(request.META.get("HTTP_REFERER", '/'))
        except Exception as e:
            print("An error occurred:", e)
            messages.warning(request, f"An error occurred: {e}")
            return redirect(request.META.get("HTTP_REFERER", '/'))




@method_decorator((login_required, vendor_required), name='dispatch')
class VendorProfileView(View):
    template_name = 'vendor/vendor_profile.html'

    def get(self, request):
        try:
            vendor = request.user.vendor_profile
            context = {
                'vendor': vendor,
                'page_name': 'vendor_profile',
            }
            return render(request, self.template_name, context)
        except Vendor.DoesNotExist:
            messages.error(request, "Your vendor profile could not be found.")
            return redirect('vendor_dashboard') # Redirect to dashboard or appropriate page
        except Exception as e:
            print(e)
            messages.error(request, f"An error occurred while fetching your profile: {e}")
            return redirect('vendor_dashboard') # Redirect to dashboard or appropriate page



@method_decorator((login_required, vendor_required), name='dispatch')
class VendorProfileEditView(View):
    template_name = 'vendor/vendor_profile_edit.html'
    form_class = VendorProfileForm

    def get(self, request):
        try:
            vendor = request.user.vendor_profile
            form = self.form_class(instance=vendor)
            context = {
                'form': form,
                'page_name': 'vendor_profile_edit',
            }
            return render(request, self.template_name, context)
        except Vendor.DoesNotExist:
            messages.error(request, "Your vendor profile could not be found.")
            return redirect('vendor_profile')
        except Exception as e:
            print(e)
            messages.error(request, f"An error occurred while fetching your profile for editing: {e}")
            return redirect('vendor_profile')

    def post(self, request):
        try:
            vendor = request.user.vendor_profile
            form = self.form_class(request.POST, instance=vendor)
            if form.is_valid():
                form.save()
                messages.success(request, "Your profile has been updated successfully.")
                return redirect('vendor_profile')
            else:
                context = {
                    'form': form,
                    'page_name': 'vendor_profile_edit',
                }
                return render(request, self.template_name, context)
        except Vendor.DoesNotExist:
            messages.error(request, "Your vendor profile could not be found.")
            return redirect('vendor_profile')
        except Exception as e:
            messages.error(request, f"An error occurred while updating your profile: {e}")
            return redirect('vendor_profile')




@method_decorator((login_required, vendor_required), name='dispatch')
class PaymentListView(View):
    template_name = 'vendor/payment_list.html'

    def get(self, request):
        try:
            vendor = request.user.vendor_profile
            payments = Payment.objects.filter(order__vendor=vendor).order_by('-order__order_date')

             # Prepare data for Payment Method Chart
            payment_methods_data = Payment.objects.filter(order__vendor=vendor).values('payment_method').annotate(count=Count('payment_method'))
            payment_method_labels = [item['payment_method'] for item in payment_methods_data]
            payment_method_counts = [item['count'] for item in payment_methods_data]

            # Prepare data for Payment Status Chart
            payment_statuses_data = Payment.objects.filter(order__vendor=vendor).values('payment_status').annotate(count=Count('payment_status'))
            payment_status_labels = [item['payment_status'] for item in payment_statuses_data]
            payment_status_counts = [item['count'] for item in payment_statuses_data]


            context = {
                'payments': payments,
                'page_name': 'payment_list',
                'payment_methods_data': {
                    'labels': payment_method_labels,
                    'data': payment_method_counts,
                },
                'payment_statuses_data': {
                    'labels': payment_status_labels,
                    'data': payment_status_counts,}
            }
            return render(request, self.template_name, context)
        except Exception as e:
            messages.error(request, f"An error occurred while fetching payments: {e}")
            return redirect('vendor_dashboard')

    def post(self, request):
        if 'payment_id' in request.POST and 'status' in request.POST:
            payment_id = request.POST['payment_id']
            new_status = request.POST['status']

            if new_status in [status[0] for status in Payment._meta.get_field('payment_status').choices]:
                try:
                    payment = get_object_or_404(Payment, payment_id=payment_id, order__vendor__user=request.user)
                    payment.payment_status = new_status
                    payment.order.is_complete = True
                    payment.save()
                    
                    messages.success(request, f"Payment status for Order #{payment.order.order_id} updated to {new_status}.")
                except Exception as e:
                    messages.error(request, f"Error updating payment status: {e}")
            else:
                messages.error(request, "Invalid payment status.")

        return redirect('vendor_payments')



@method_decorator((login_required, customer_required), name='dispatch')
class CustomerPaymentListView(View):
    template_name = 'customer/customer_payment_list.html'

    def get(self, request):
        try:
            customer = request.user
            payments = Payment.objects.filter(order__customer=customer).order_by('-order__order_date')

            # Monthly Analysis
            monthly_analysis = Payment.objects.filter(order__customer=customer).annotate(month=TruncMonth('order__order_date')).values('month').annotate(total_payments=Count('payment_id'), total_amount=Sum('amount')).order_by('month')
            monthly_data = [{'month': item['month'].strftime('%Y-%m'), 'payments': item['total_payments'], 'amount': float(item['total_amount'])} for item in monthly_analysis]

            # Weekly Analysis
            weekly_analysis = Payment.objects.filter(order__customer=customer).annotate(week=TruncWeek('order__order_date')).values('week').annotate(total_payments=Count('payment_id'), total_amount=Sum('amount')).order_by('week')
            weekly_data = [{'week': item['week'].strftime('%Y-W%W'), 'payments': item['total_payments'], 'amount': float(item['total_amount'])} for item in weekly_analysis]

            # Yearly Analysis
            yearly_analysis = Payment.objects.filter(order__customer=customer).annotate(year=TruncYear('order__order_date')).values('year').annotate(total_payments=Count('payment_id'), total_amount=Sum('amount')).order_by('year')
            yearly_data = [{'year': item['year'].strftime('%Y'), 'payments': item['total_payments'], 'amount': float(item['total_amount'])} for item in yearly_analysis]

            context = {
                'payments': payments,
                'page_name': 'customer_payment_list',
                'monthly_data_json': json.dumps(monthly_data),
                'weekly_data_json': json.dumps(weekly_data),
                'yearly_data_json': json.dumps(yearly_data),
            }
            return render(request, self.template_name, context)
        except Exception as e:
            messages.error(request, f"An error occurred while fetching your payments: {e}")
            return redirect('customer_dashboard')

    def post(self, request):
        if 'payment_id' in request.POST and 'action' in request.POST and request.POST['action'] == 'paid':
            payment_id = request.POST['payment_id']
            try:
                payment = get_object_or_404(Payment, payment_id=payment_id, order__customer=request.user)
                if payment.payment_status == 'Pending':
                    payment.payment_status = 'Pending Confirmation'
                    payment.save()
                    messages.success(request, f"You have indicated that you have paid for Order #{payment.order.order_id}. The vendor will confirm.")
                else:
                    messages.info(request, f"You have already indicated payment for Order #{payment.order.order_id}.")
            except Exception as e:
                messages.error(request, f"Error updating payment status: {e}")

        return redirect('customer_payments')


#delivery tracking stuffs


@csrf_exempt  # Consider security implications in production
@login_required  # Ensure only logged-in drivers can update
def update_driver_location(request, delivery_id):
    if request.method == 'POST':
        try:
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            delivery = get_object_or_404(Delivery, delivery_id=delivery_id, driver=request.user.driver_profile) # Assuming driver is linked to user

            if latitude and longitude:
                delivery.driver_current_lat = latitude
                delivery.driver_current_lng = longitude
                delivery.save()
                return JsonResponse({'status': 'success', 'message': 'Driver location updated successfully'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Latitude and longitude are required'}, status=400)
        except Delivery.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Delivery not found or not assigned to this driver'}, status=404)
        except Exception as e:
            print(e)
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

# Similar view to update customer's initial location (if needed)
@csrf_exempt
def update_customer_location(request, delivery_id):
    if request.method == 'POST':
        try:
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            delivery = get_object_or_404(Delivery, delivery_id=delivery_id, order__customer=request.user) # Assuming customer is linked to user

            if latitude and longitude:
                delivery.customer_lat = latitude
                delivery.customer_lng = longitude
                delivery.save()
                return JsonResponse({'status': 'success', 'message': 'Customer location updated successfully'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Latitude and longitude are required'}, status=400)
        except Delivery.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Delivery not found for this customer'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)





@login_required
def get_delivery_status(request, delivery_id):
    try:
        delivery = get_object_or_404(Delivery, delivery_id=delivery_id)
        data = {
            'delivery_status': delivery.delivery_status,
            'is_delivered': delivery.is_deleivered,
            'driver_lat': float(delivery.driver_current_lat) if delivery.driver_current_lat else None,
            'driver_lng': float(delivery.driver_current_lng) if delivery.driver_current_lng else None,
            'customer_lat': float(delivery.customer_lat) if delivery.customer_lat else None,
            'customer_lng': float(delivery.customer_lng) if delivery.customer_lng else None,
            'estimated_arrival_time': delivery.estimated_arrival_time.isoformat() if delivery.estimated_arrival_time else None,
            'last_updated': delivery.last_updated.isoformat() if delivery.last_updated else None,
        }
        return JsonResponse(data)
    except Delivery.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Delivery not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)





@login_required
def customer_track_delivery(request, delivery_id):
    delivery = get_object_or_404(Delivery, delivery_id=delivery_id, order__customer=request.user)
    context = {'delivery': delivery}
    return render(request, 'customer/track_delivery.html', context)

@login_required
def driver_track_delivery(request, delivery_id):
    if not request.user.is_driver or request.user.is_admin:
        messages.info(request, f"Access Denied ..")
        return redirect('home')
    delivery = get_object_or_404(Delivery, delivery_id=delivery_id, driver=request.user.driver_profile)
    context = {'delivery': delivery}
    return render(request, 'driver/track_delivery.html', context)




@method_decorator((login_required,customer_required), name='dispatch')
class CustomerDeliveryListView(View):
    template_name = 'customer/customer_delivery_list.html'

    def get(self, request):
        customer = request.user
        deliveries = Delivery.objects.filter(order__customer=customer).order_by('-delivery_date')
        context = {
            'deliveries': deliveries,
            'page_name': 'customer_deliveries',
        }
        return render(request, self.template_name, context)



@method_decorator((login_required,driver_required), name='dispatch')
class DriverDeliveryListView(View):
    template_name = 'driver/delivery_delivery_list.html'

    def get(self, request):
        driver = request.user.driver_profile
        deliveries = Delivery.objects.filter(driver=driver).order_by('-delivery_date')
        context = {
            'deliveries': deliveries,
            'page_name': 'customer_deliveries',
        }
        return render(request, self.template_name, context)




from django.shortcuts import render, get_object_or_404
from .models import Delivery  # Import your Delivery model
from django.contrib.auth.decorators import login_required

@login_required
def test_customer_delivery_tracking(request, delivery_id):
    """
    View function to display the delivery tracking page for a customer.
    """
    try:
        delivery = Delivery.objects.get(delivery_id=delivery_id)  # Fetch the Delivery object
    except Delivery.DoesNotExist:
        #  Handle the case where the delivery_id is invalid
        #  You might want to display a user-friendly error message
        return render(request, 'customer/delivery_not_found.html', {'delivery_id': delivery_id}, status=404)

    # Check if the current user is the customer for this delivery
    if delivery.order.customer != request.user:
        return render(request, 'customer/delivery_access_denied.html', {'delivery_id': delivery_id}, status=403)

    context = {
        'delivery': delivery,  # Pass the Delivery object to the template
    }
    return render(request, 'test/customer_delivery_tracking.html', context)  # Render the template

@login_required
def test_driver_delivery_tracking(request, delivery_id):
    """
    View function to display the delivery tracking page for a driver.
    """
    try:
        delivery = Delivery.objects.get(delivery_id=delivery_id)
    except Delivery.DoesNotExist:
        return render(request, 'driver/delivery_not_found.html', {'delivery_id': delivery_id}, status=404)

    # Check if the current user is the driver for this delivery
    if delivery.driver.user != request.user:
        return render(request, 'driver/delivery_access_denied.html', {'delivery_id': delivery_id}, status=403)

    context = {
        'delivery': delivery,
    }
    return render(request, 'test/delivery_tracking.html', context)
