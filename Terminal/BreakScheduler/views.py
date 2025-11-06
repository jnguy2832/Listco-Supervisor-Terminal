from django.shortcuts import render

def index(request):
    return render(request, 'dashboard.html')

def weeklyPortal(request):
    return render(request, 'schedule.html')

def breaks(request):
    return render(request, 'breaks.html')

def candy(request):
    return render(request, 'candy.html')

def carts(request):
    return render(request, 'carts.html')

def haba(request):
    return render(request, 'haba.html')

def gasStation(request):
    return render(request, 'gas_station.html')

def walk(request):
    return render(request, 'walk.html')