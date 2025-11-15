import json, time, queue
from django.shortcuts import render
from django.utils import timezone
from .models import *
from .services import BreakService
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def index(request):
    return render(request, 'dashboard.html')

def weeklyPortal(request):
    return render(request, 'schedule.html')

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
            if action == 'start_break':
                BreakService.startBreak(break_obj)
                # Broadcast the update via WebSocket
                broadcast_break_update(break_obj)
            elif action == 'end_break':
                BreakService.endBreak(break_obj)
            # (INSERT SUCCESS MESSAGE / messages framework if desired)
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
        'current_time': now,
        'on_break_ids': on_break_ids,
        'shifts_on_break_ids': shifts_on_break_ids,
    }

    return render(request, 'breaks.html', context)

def broadcast_break_update(break_obj):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
    'breaks_updates',
        {
            'type': 'break_status_update',
            'break_id': break_obj.id,
            'status': break_obj.status,
            'break_start': break_obj.break_start.isoformat() if break_obj.break_start else None,
            'break_end': break_obj.break_end.isoformat() if break_obj.break_end else None,
            'employee_name': f"{break_obj.shift.employee.first_name} {break_obj.shift.employee.last_name}",
            'type': break_obj.break_type
        }
    )
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