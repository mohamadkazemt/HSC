from django.contrib import admin
from .models import Contractor, Employee, Vehicle


class EmployeeInline(admin.TabularInline):
    model = Employee
    fields = ('first_name', 'last_name', 'national_id', 'position', 'phone_number', 'user')
    extra = 0
    raw_id_fields = ('user',)


@admin.register(Contractor)
class ContractorAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'manager_name', 'manager_phone', 'user', 'liability_insurance', 'fire_insurance')
    search_fields = ('company_name', 'manager_name', 'user__username')
    raw_id_fields = ('user',)
    inlines = [EmployeeInline]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'national_id', 'phone_number', 'contractor', 'user', 'education', 'position', 'entry_permit_expiration')
    search_fields = ('first_name', 'last_name', 'national_id', 'user__username')
    raw_id_fields = ('user', 'contractor')


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle_type', 'license_plate', 'insurance_expiry', 'contractor', 'technical_inspection_expiry', 'driver_name', 'permit_expiry')
    search_fields = ('license_plate', 'vehicle_type')


