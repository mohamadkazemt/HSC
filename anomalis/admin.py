from django.contrib import admin
from anomalis.models import CorrectiveAction
from .models import Location, Anomalytype, Tags




admin.site.register(Location)
admin.site.register(Anomalytype)
admin.site.register(CorrectiveAction)
admin.site.register(Tags)



