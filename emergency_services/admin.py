from django.contrib import admin
from .models import (
    MedicalVisit, 
    MedicineUsage, 
    Medicine, 
    MedicineCategory, 
    MedicalService,
    MedicineReturn,
    Hospital
)


class MedicineUsageInline(admin.TabularInline):
    model = MedicineUsage
    extra = 0
    readonly_fields = ('created_at',)


class MedicineReturnInline(admin.TabularInline):
    model = MedicineReturn
    extra = 0
    readonly_fields = ('created_at',)
    fk_name = 'usage'


@admin.register(MedicalVisit)
class MedicalVisitAdmin(admin.ModelAdmin):
    list_display = ('get_person_name', 'personnel_type', 'visit_time', 'created_by', 'created_at')
    list_filter = ('personnel_type', 'visit_time', 'created_at')
    search_fields = ('visit_reason', 'doctor_recommendation')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('services',)
    inlines = [MedicineUsageInline]
    
    def get_person_name(self, obj):
        if obj.personnel_type == 'company':
            return obj.company_personnel.get_full_name() if obj.company_personnel else "بدون نام"
        else:
            return str(obj.contractor_personnel) if obj.contractor_personnel else "بدون نام"
    get_person_name.short_description = 'نام مراجعه کننده'


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity', 'critical_threshold', 'expiry_date', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name',)
    list_editable = ('quantity', 'critical_threshold', 'is_active')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(MedicineCategory)
class MedicineCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


@admin.register(MedicalService)
class MedicalServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


@admin.register(MedicineUsage)
class MedicineUsageAdmin(admin.ModelAdmin):
    list_display = ('medicine', 'quantity', 'visit', 'created_at')
    list_filter = ('medicine', 'created_at')
    search_fields = ('medicine__name',)
    readonly_fields = ('created_at',)
    inlines = [MedicineReturnInline]


@admin.register(MedicineReturn)
class MedicineReturnAdmin(admin.ModelAdmin):
    list_display = ('usage', 'quantity', 'return_reason', 'returned_by', 'created_at')
    list_filter = ('returned_by', 'created_at')
    search_fields = ('return_reason', 'usage__medicine__name')
    readonly_fields = ('created_at',)


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'phone', 'address')
    ordering = ('-created_at',) 