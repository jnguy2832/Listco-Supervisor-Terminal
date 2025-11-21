import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Break, Shift
from django.utils import timezone
from channels.db import database_sync_to_async

class BreakUpdateConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'breaks_updates'

        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )
        await self.accept()

        initial_data = await self.get_current_breaks()
        await self.send(text_data=json.dumps({
            'type': 'initial_data',
            'breaks': initial_data
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'update':
            current_breaks = await self.get_current_breaks()
            await self.send(text_data=json.dumps({
                'type': 'breaks_update',
                'breaks': current_breaks
            }))
    
    async def break_status_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'break_update',
            'break_id': event['break_id'],
            'status': event['status'],
            'break_start': event.get('break_start'),
            'break_end': event.get('break_end'),
            'employee_name': event.get('employee_name'),
            'break_type': event.get('break_type')
        }))

    @database_sync_to_async
    def get_current_breaks(self):
        today = timezone.localdate()
        start_of_day = timezone.make_aware(
            timezone.datetime.combine(today, timezone.datetime.min.time())
        )
        end_of_day = timezone.make_aware(
            timezone.datetime.combine(today, timezone.datetime.max.time())
        )
        shifts = Shift.objects.filter(
            start_time__lte=end_of_day,
            end_time__gte=start_of_day
        ).select_related('employee').prefetch_related('break_set')

        breaks_data = []
        for shift in shifts:
            employee_name = f"{shift.employee.first_name} {shift.employee.last_name}"
            related_breaks = list(shift.break_set.all())
            if related_breaks:
                for break_obj in related_breaks:
                    breaks_data.append({
                        'id': break_obj.id,
                        'employee_name': employee_name,
                        'break_type': break_obj.break_type,
                        'break_start': break_obj.break_start.isoformat() if break_obj.break_start else None,
                        'break_end': break_obj.break_end.isoformat() if break_obj.break_end else None,
                        'status': break_obj.status,
                        'shift_id': shift.id,
                        'shift_start': shift.start_time.isoformat() if shift.start_time else None,
                        'shift_end': shift.end_time.isoformat() if shift.end_time else None,
                        'location': shift.employee.location if getattr(shift.employee, 'location', None) else None
                    })
            else:
                # No break objects were created for this shift; send a placeholder so UI can show the shift
                breaks_data.append({
                    'id': None,
                    'employee_name': employee_name,
                    'break_type': None,
                    'break_start': shift.start_time.isoformat() if shift.start_time else None,
                    'break_end': shift.end_time.isoformat() if shift.end_time else None,
                    'status': 'No breaks scheduled',
                    'shift_id': shift.id,
                    'shift_start': shift.start_time.isoformat() if shift.start_time else None,
                    'shift_end': shift.end_time.isoformat() if shift.end_time else None,
                    'location': shift.employee.location if getattr(shift.employee, 'location', None) else None
                })

        return breaks_data