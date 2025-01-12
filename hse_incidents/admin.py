from django.contrib import admin

# Register your models here.
from .models import IncidentReport, InjuryType

admin.site.register(IncidentReport)
admin.site.register(InjuryType)