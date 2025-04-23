from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'home.html')


def signin(request):
    return render(request, 'signin.html')

def customer_dashboard(request):
    return render(request, 'customer_dashboard.html')