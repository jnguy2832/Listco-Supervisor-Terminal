from django.utils import timezone
from datetime import timedelta
from django_q.tasks import schedule
from django_q.models import Schedule
from .models import *
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class BreakService:
    @staticmethod
    def broadcast_break_update(break_obj):
        #Method to update break for client
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                'breaks_updates',
                {
                    'type': 'break_status_update',
                    'break_id': break_obj.id,
                    'status': break_obj.status,
                    'break_start': break_obj.break_start.isoformat() if break_obj.break_start else None,
                    'break_end': break_obj.break_end.isoformat() if break_obj.break_end else None,
                    'employee_name': f"{break_obj.shift.employee.first_name} {break_obj.shift.employee.last_name}",
                    'break_type': break_obj.break_type
                }
            )


    #Event for break reaching 'minutesLeftAlert' time left.
    #Status hardcoded as 5 minutes for business needs but possible to be dynamic if needed.
    @staticmethod
    def breakEnding(break_id):
        try:
            breakObject = Break.objects.get(id=break_id)
            employeeBreak = breakObject.shift.employee

            breakObject.status = '5 minutes left'
            breakObject.save()

            
            #Websocket broadcast for breakEnding
            BreakService.broadcast_break_update(breakObject)

            #Schedules task end after warning, logic goes breakStart > breakEnding > breakEnded
            ended_task_id = schedule(
                'BreakScheduler.services.BreakService.breakEnded',
                breakObject.id,
                schedule_type = Schedule.ONCE,
                next_run = breakObject.break_end,
                name = (f'Break #{breakObject.id} : {breakObject.shift.employee.last_name}')
            )


            return "Break notification test"
        except Break.DoesNotExist:
            print("Break not found")
            return -1
    
    @staticmethod
    def breakEnded(break_id):
        try:
            breakObject = Break.objects.get(id=break_id)
            employeeBreak = breakObject.shift.employee

            BreakService.broadcast_break_update(breakObject)

            breakObject.status = 'Over'
            breakObject.save()

            return "Break ending now"
        except Break.DoesNotExist:
            print("Break not found")
            return -1

    #Starts break of breakObject and determines when breakEnding function should run with minutesLeftAlert
    @staticmethod
    def startBreak(breakObject, minutesLeftAlert=5):
        breakObject.break_start = timezone.now()
        breakObject.status = 'On Break'
        breakObject.save()
        
        BreakService.broadcast_break_update(breakObject)

        Schedule.objects.filter(name__contains=f'Break #{breakObject.id}').delete()

        if breakObject.break_end:
            reminderTime = breakObject.break_end - timedelta(minutes=minutesLeftAlert)

            if reminderTime > timezone.now():
                warning_task_id = schedule(
                    'BreakScheduler.services.BreakService.breakEnding',
                    breakObject.id,
                    schedule_type = Schedule.ONCE,
                    next_run = reminderTime,
                    name=(f'Break #{breakObject.id} : {breakObject.shift.employee.last_name}'),
                )
        return warning_task_id

    #Deletes django_q schedule for breakObject when break ends. Output string only for testing.
    @staticmethod
    def endBreak(breakObject):
        Schedule.objects.filter(
            func__in=['BreakScheduler.services.BreakService.breakEnding',
                      'BreakScheduler.services.BreakService.breakEnded'],
            name__contains=f'Break #{breakObject.id}'
        ).delete()

        breakObject.status = 'Over'
        breakObject.save()

        BreakService.broadcast_break_update(breakObject)

        print("Schedule has been ended for ", breakObject.shift.employee.last_name)
        return "Schedule ended"