from django.contrib import admin
from anomalis.models import CorrectiveAction, Anomaly, AnomalyDescription, HSE, Comment
from .models import Location, Anomalytype, Priority
from .views import anomaly_list

admin.site.register(Anomaly)

admin.site.register(Location)
admin.site.register(Anomalytype)
admin.site.register(CorrectiveAction)
admin.site.register(Priority)
admin.site.register(AnomalyDescription)
admin.site.register(HSE)
admin.site.register(Comment)
