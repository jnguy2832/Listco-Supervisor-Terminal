import json, time, queue
from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib import messages
from .models import *
from .services import BreakService
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import datetime
from datetime import timedelta

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
                end_dt_naive = datetime.datetime.combine(shift_date + timedelta(days=1), end_time_obj)
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
    
    #determine the start of the week
    #check if the user selected a specific date via URL
    selected_date_str = request.GET.get('date')

    if selected_date_str:
        current_date = datetime.datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    else:
        current_date = timezone.localdate()

    #Calculate start of the week
    #Sunday is day 0
    #(current_date.weekday() + 1) % 7 gives us how many days past sunday we are
    days_to_subtract = (current_date.weekday() + 1) % 7
    start_of_week = current_date - timedelta(days=days_to_subtract)
    end_of_week = start_of_week + timedelta(days=6)

    #Weekly Schedule datastructure
    #Fetches all employees so that even those with 0 hours appears on the schedule
    employees = Employee.objects.all().order_by('job_title')

    #dictionary for quick lookup
    schedule_map = {}
    for emp in employees:
        schedule_map[emp.id] = {
            'employee': emp,
            'total_hours': 0,
            'shifts': {
                'Sunday': '', 'Monday': '', 'Tuesday': '', 'Wednesday': '',
                'Thursday': '', 'Friday': '', 'Saturday': ''
            }
        }
    
    #Fetch shifts for this week
    #Make range timezone aware for the query
    start_aware = timezone.make_aware(datetime.datetime.combine(start_of_week, datetime.datetime.min.time()))
    end_aware = timezone.make_aware(datetime.datetime.combine(end_of_week, datetime.datetime.max.time()))

    # Include any shifts that overlap the week (start before end_of_week and end after start_of_week)
    weekly_shifts = Shift.objects.filter(
        start_time__lte=end_aware,
        end_time__gte=start_aware
    ).select_related('employee')

    #Populate the weekly map
    for shift in weekly_shifts:
        emp_id = shift.employee.id
        if emp_id in schedule_map:
            #Calculate hours for specific shift
            duration = shift.end_time - shift.start_time
            hours = duration.total_seconds() / 3600
            # Use emp_id (from the current shift) to update the correct employee entry
            schedule_map[emp_id]['total_hours'] += hours

            #format the time string (e.g., "09:00 AM - 05:30 PM")
            # Use timezone.localtime to render times in the active timezone
            start_local = timezone.localtime(shift.start_time)
            end_local = timezone.localtime(shift.end_time)
            start_str = start_local.strftime("%I:%M %p")
            end_str = end_local.strftime("%I:%M %p")
            time_display = f"{start_str} - {end_str}"

            #Determine the day name (e.g., "Monday") using localized start
            day_name = start_local.strftime("%A")

            #Assigns to the specific day slot
            #We append incase they have two shifts in one day (e.g. a split shift)
            if schedule_map[emp_id]['shifts'][day_name]:
                schedule_map[emp_id]['shifts'][day_name] += f"<br>{time_display}"
            else:
                schedule_map[emp_id]['shifts'][day_name] = time_display
    #Convert map back into a list for the template to loop through
    for item in schedule_map.values():
        item['total_hours'] = round(item['total_hours'], 2)
    schedule_data = list(schedule_map.values())

    #Total Department Hours
    Total_Department_hours = sum(item['total_hours'] for item in schedule_data)
    
    # Gets employees for the dropdown list
    employees = Employee.objects.all().order_by('last_name')

    context = {
        'employees': employees,
        'schedule_data': schedule_data,
        'week_start': start_of_week,
        'week_end': end_of_week,
        'total_department_hours': Total_Department_hours,
    }

    return render(request, 'schedule.html', context)

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