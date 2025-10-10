from django.shortcuts import render

def index(request):
    return render(request, 'dashboard.html')
def break_view(request):
    return render(request, 'break.html')

