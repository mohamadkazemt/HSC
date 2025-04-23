from django.contrib import admin
from .models import InitialShiftSetup

@admin.register(InitialShiftSetup)
class InitialShiftSetupAdmin(admin.ModelAdmin):
    list_display = ('start_date', 'group_A_shift', 'group_B_shift', 'group_C_shift', 'group_D_shift')




