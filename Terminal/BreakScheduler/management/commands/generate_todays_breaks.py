from django.core.management.base import BaseCommand
from BreakScheduler.models import Shift
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = "Generates break schedules for all shifts scheduled for today"

    def handle(self, *args, **options):
        #define today's start and end times
        today = timezone.localdate()
        start_of_day = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
        end_of_day = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.max.time()))

        #Get shifts that start today
        shifts_to_schedule = Shift.objects.filter(
            start_time__gte=start_of_day,
            start_time__lte=end_of_day
        )

        self.stdout.write(self.style.NOTICE(f'Found {shifts_to_schedule.count()} shifts for today'))

        count = 0
        for shift in shifts_to_schedule:
            try:
                shift.generate_breaks()
                shift.is_scheduled = True
                shift.save()
                count += 1
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Failed to generate breaks for Shift ID {shift.id}: {e}'))
            self.stdout.write(self.style.SUCCESS(f'Successfully generated breaks for {count} shifts.'))