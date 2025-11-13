from django.shortcuts import render
from django.utils import timezone
from .models import Shift, Break
from .services import BreakService

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

    #Handle Break Action first (so we render fresh data after any state change)
    if request.method == 'POST':
        action = request.POST.get('action')
        break_id = request.POST.get('break_id')

        try:
            break_obj = Break.objects.get(pk=break_id)
            if action == 'start_break':
                BreakService.startBreak(break_obj)
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

    # Determine which shifts have any active breaks (used to highlight shift rows)
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