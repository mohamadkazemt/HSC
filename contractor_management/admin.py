from django.contrib import admin
from .models import Contractor, Employee, Vehicle



@admin.register(Contractor)
class ContractorAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'manager_name', 'manager_phone', 'liability_insurance', 'fire_insurance')
    search_fields = ('company_name', 'manager_name')


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'national_id', 'phone_number', 'contractor', 'education', 'position', 'health_certificate', 'background_check', 'safety_training', 'other_trainings', 'entry_permit_expiration')
    search_fields = ('first_name', 'last_name', 'national_id')


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle_type', 'license_plate', 'insurance_expiry', 'contractor', 'technical_inspection_expiry', 'driver_name', 'permit_expiry')
    search_fields = ('license_plate', 'vehicle_type')


