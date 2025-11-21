import json, time, queue
from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib import messages
from .models import *
from .services import BreakService
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import datetime

def index(request):
    return render(request, 'dashboard.html')

def weeklyPortal(request):
    # Form data for button
    if request.method == 'POST':
        employee_id = request.POST.get('employee')
        shift_date_str = request.POST.get('shift_date')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')

        try:
            employee = Employee.objects.get(id=employee_id)
            # Parse strings into python objects
            shift_date = datetime.datetime.strptime(shift_date_str, "%Y-%m-%d").date()
            start_time_obj = datetime.datetime.strptime(start_time_str, "%H:%M").time()
            end_time_obj = datetime.datetime.strptime(end_time_str, "%H:%M").time()

            # combine into timezone aware datetimes
            start_dt_naive = datetime.datetime.combine(shift_date, start_time_obj)
            if end_time_obj < start_time_obj:
                end_dt_naive = datetime.datetime.combine(shift_date + datetime.timeedelta(days=1), end_time_obj)
            else:
                end_dt_naive = datetime.datetime.combine(shift_date, end_time_obj)

            start_dt = timezone.make_aware(start_dt_naive)
            end_dt = timezone.make_aware(end_dt_naive)

            # Create Shift and Generate Breaks
            new_shift = Shift(
                employee=employee,
                start_time=start_dt,
                end_time=end_dt,
                is_scheduled=True
            )
            new_shift.save()

            new_shift.refresh_from_db()

            # calls model method to create the break objects
            new_shift.generate_breaks()
            messages.success(request, f"Shift assigned to {employee.first_name} {employee.last_name}.")
        except Exception as e:
            messages.error(request, f"Error assigning shift: {e}")
        return redirect('Schedule')
    
    # Gets employees for the dropdown list
    employees = Employee.objects.all().order_by('last_name')
    return render(request, 'schedule.html', {'employees': employees})

def breaks(request):
    #Displays all shifts and their generated breaks
    
    #Define today's time range
    today = timezone.localdate()
    start_of_day = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
    end_of_day = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.max.time()))

    if request.method == 'POST':
        action = request.POST.get('action')
        break_id = request.POST.get('break_id')

        try:
            break_obj = Break.objects.get(pk=break_id)
            if action =='start_break':
                BreakService.startBreak(break_obj)
            elif action == 'end_break':
                BreakService.endBreak(break_obj)
            #(INSERT SUCCESS MESSAGE HERE)
        except Break.DoesNotExist:
            pass

    #Fetch all shifts for today, ordered by start time (fresh after any POST)
    todays_shifts = Shift.objects.filter(
        start_time__gte=start_of_day,
        start_time__lte=end_of_day
    ).select_related('employee__job_title').prefetch_related('break_set').order_by('start_time')

    # Determine which breaks are currently in-progress so the template can highlight them
    now = timezone.now()
    on_break_ids = []
    for s in todays_shifts:
        for b in s.break_set.all():
            if b.status == 'On Break':
                on_break_ids.append(b.id)
            elif b.break_start and b.break_end and (b.break_start <= now <= b.break_end):
                on_break_ids.append(b.id)

    shifts_on_break_ids = []
    for s in todays_shifts:
        for b in s.break_set.all():
            if b.id in on_break_ids:
                shifts_on_break_ids.append(s.id)
                break

    context = {
        'shifts_today': todays_shifts,
        'current_time': timezone.now()
    }
    return render(request, 'breaks.html', context)

def supervisor(request):
    return render(request, 'supervisors.html')

def carts(request):
    return render(request, 'carts.html')

def cashier(request):
    return render(request, 'cashiers.html')

def gasStation(request):
    return render(request, 'gas_station.html')

def food_court(request):
    return render(request, 'food_court.html')