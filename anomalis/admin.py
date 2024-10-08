from django.contrib import admin
from anomalis.models import CorrectiveAction, Anomaly
from .models import Location, Anomalytype, Priority

admin.site.register(Anomaly)

admin.site.register(Location)
admin.site.register(Anomalytype)
admin.site.register(CorrectiveAction)
admin.site.register(Priority)