from django.contrib import admin

from .models import JobTitle, Employee, Shift, Break

admin.site.register(JobTitle)
admin.site.register(Employee)
admin.site.register(Shift)
admin.site.register(Break)