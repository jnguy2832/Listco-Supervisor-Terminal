from django.db import models
from django.utils import timezone
from datetime import timedelta

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
    end_time = models.DateTimeField

    #store the actual shift length in num of minutes. e.g. 8 hrs = 480 mins
    shift_len = models.IntegerField(default=0)
    #scheduled?
    is_scheduled = models.BooleanField(default=False)
    def __str__(self):
        return f"shift for {self.employee.first_name} {self.employee.last_name} on {self.start_time.date()}"