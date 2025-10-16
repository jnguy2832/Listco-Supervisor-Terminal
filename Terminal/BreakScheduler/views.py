from django.shortcuts import render

def index(request):
    return render(request, 'dashboard.html')

def breakPortal(request):
    return render(request, 'break.html')

def candy(request):
    return render(request, 'candy.html')

def carts(request):
    return render(request, 'carts.html')