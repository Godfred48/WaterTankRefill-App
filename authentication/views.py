from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'home.html')


def signin(request):
    return render(request, 'signin.html')

def customer_dashboard(request):
    return render(request, 'customer_dashboard.html')

def about(request):
    return render(request, 'about.html')

def services(request):
    return render(request, 'services.html')

def signup(request):
    return render(request, 'signup.html')

def orders(request):
    return render(request, 'orders.html')