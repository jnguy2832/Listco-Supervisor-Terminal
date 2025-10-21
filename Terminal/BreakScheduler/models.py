from django.db import models
from django.utils import timezone
from datetime import timedelta
from .scheduler_constants import break_15_minutes, meal_30_minutes, break_rules

class JobTitle(models.Model):
    title = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.title

class Employee(models.Model):
    #Represents an employee
    employee_id_num = models.CharField(max_length=20)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    job_title = models.ForeignKey(JobTitle, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} {self.job_title}"

class Shift(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    #store the actual shift length in num of minutes. e.g. 8 hrs = 480 mins
    shift_len = models.IntegerField(default=0)
    #scheduled?
    is_scheduled = models.BooleanField(default=False)
    def __str__(self):
        return f"shift for {self.employee.first_name} {self.employee.last_name} on {self.start_time.date()}"
    
    #method to calculate total shift duration and find break requirements
    def calculate_break_requirments(self):
        #calculate total duration
        duration = self.end_time - self.start_time
        #convert total duration to hours
        total_hours = duration.total_seconds() / 3600

        required_breaks = {'15': 0, '30' : 0}

        #iterate through the rules to find the highest duration met
        for min_hours, counts in sorted(break_rules.items()):
            if total_hours >= min_hours:
                required_breaks = counts

        return required_breaks, total_hours

    def generate_breaks(self):
        # 1. clear any existing breaks for this shift
        self.break_set.all().delete()
        
        required_breaks, total_hours = self.calculate_break_requirments()

        if total_hours < 4:
            return #no breaks for shifts less than 4 hours

        breaks_to_schedule = []
        for _ in range(required_breaks['30']):
            breaks_to_schedule.append(('M30', meal_30_minutes))
        for _ in range(required_breaks['15']):
            breaks_to_schedule.append(('15', break_15_minutes))

        #total working time (excluding unpaid 30 min meal)
        paid_working_minutes = total_hours * 60
        if required_breaks['30'] > 0:
            paid_working_minutes -= meal_30_minutes

        #total duration of all breaks to be taken
        total_break_time = sum(item[1] for item in breaks_to_schedule)
        
        #total elapsed time during shift including breaks
        total_elapsed_time = total_hours * 60

        #determine intervals for even distribution (need n+1 intervals for n breaks)
        N = len(breaks_to_schedule)
        if N == 0:
            return

        #divide the shift time into N+1 even slots
        interval_minutes = total_elapsed_time / (N + 1)

        current_time = self.start_time
        scheduled_breaks = []

        # 3. schedule the breaks
        for i, (break_type, duration) in enumerate(breaks_to_schedule):
            # The break should start roughly 'interval_minutes' after the previous break/start of shift
            # We use i+1 because the first break is after the first interval.
            target_start_offset = timedelta(minutes=interval_minutes * (i + 1))

            #calculate break start and end time
            break_start = self.start_time + target_start_offset
            break_end = break_start + timedelta(minutes=duration)

            scheduled_breaks.append(Break(
                shift=self,
                break_type=break_type,
                break_start=break_start,
                break_end=break_end
            ))

        # 4. Save to database
        Break.objects.bulk_create(scheduled_breaks)
    
class Break(models.Model):
    BREAK_TYPES = [
        ('15', '15 minute break'),
        ('M30', '30 minute meal')
    ]

    break_id = models.CharField(max_length=5)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    break_type = models.CharField(max_length=3, choices=BREAK_TYPES)
    break_start = models.DateTimeField(null=True, blank=True)
    break_end = models.DateTimeField(null=True, blank=True)

    #Tracks whether the break was taken or assigned
    status=models.CharField(max_length=20, default='Assigned')

    def __str__(self):
        return f"{self.break_type} for {self.shift.employee.last_name}"