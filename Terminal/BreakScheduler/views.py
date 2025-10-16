from django.shortcuts import render

def index(request):
    return render(request, 'dashboard.html')

def breakPortal(request):
    return render(request, 'break.html')