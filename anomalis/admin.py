from django.contrib import admin
from anomalis.models import Anomaly
from .models import Location, Anomalytype

class AnomalyAdmin(admin.ModelAdmin):
    list_display = ('location', 'anomalytype', 'created_by', 'followup', 'description')
    list_filter = ('location', 'anomalytype', 'created_by', 'followup', 'description')
    search_fields = ('location', 'anomalytype', 'created_by', 'followup', 'description')
    ordering = ('location', 'anomalytype', 'created_by', 'followup', 'description')

admin.site.register(Anomaly, AnomalyAdmin)




admin.site.register(Location)
admin.site.register(Anomalytype)