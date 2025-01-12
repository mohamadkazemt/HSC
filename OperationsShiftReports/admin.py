from django.contrib import admin
from .models import LoadingOperation, ShiftReport, LoaderStatus

admin.site.register(LoadingOperation)
admin.site.register(ShiftReport)
admin.site.register(LoaderStatus)
