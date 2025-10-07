from django.db import models
from django.utils import timezone
from datetime import timedelta

class Employee(models.Model):
    #Represents an employee
    name = models.CharField(max_length=100)
    employee_id_num = models.CharField(max_length=20)
    department = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name}"

class Shift(models.Model):
    #Represents a single scheduled period of work
    employee = models.ForeignKey(Employee)