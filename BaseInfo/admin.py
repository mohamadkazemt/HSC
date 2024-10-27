# admin.py
from django.contrib import admin
from .models import MiningMachine, Contractor, ContractorVehicle, MiningBlock


admin.site.register(MiningMachine)
admin.site.register(Contractor)
admin.site.register(ContractorVehicle)
admin.site.register(MiningBlock)
