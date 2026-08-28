from django.contrib import admin

from .models import Gym, GymContract, GymInvoice, GymInvoiceAuditLog, GymInvoiceItem, GymOperator, Referral, ReferralAuditLog, ReferralUsage


class GymContractInline(admin.TabularInline):
    model = GymContract
    extra = 0

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("gym")


@admin.register(Gym)
class GymAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "phone", "gender_policy_label", "is_active")
    list_filter = ("is_active", "accepts_male", "accepts_female")
    search_fields = ("name", "code")
    inlines = (GymContractInline,)

    @admin.display(description="پذیرش جنسیت")
    def gender_policy_label(self, obj):
        _, label = obj.gender_policy()
        return label


@admin.register(GymContract)
class GymContractAdmin(admin.ModelAdmin):
    list_display = ("gym", "start_date", "end_date", "billing_policy", "price_per_referral", "billing_ready")
    list_filter = ("is_active", "billing_policy")

    @admin.display(boolean=True, description="آماده صورتحساب")
    def billing_ready(self, obj):
        return obj.is_billing_ready()


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ("referral_number", "beneficiary_full_name_snapshot", "gym", "status", "source", "valid_until")
    list_filter = ("status", "source", "gym")
    search_fields = ("referral_number", "beneficiary_full_name_snapshot", "personnel_no_snapshot", "legacy_letter_no")
    readonly_fields = tuple(field.name for field in Referral._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class TransactionRecordAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        return tuple(field.name for field in self.model._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(ReferralUsage, TransactionRecordAdmin)
admin.site.register(ReferralAuditLog, TransactionRecordAdmin)
admin.site.register(GymOperator)


class GymInvoiceItemInline(admin.TabularInline):
    model = GymInvoiceItem
    extra = 0
    can_delete = False
    readonly_fields = tuple(field.name for field in GymInvoiceItem._meta.fields)


@admin.register(GymInvoice)
class GymInvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "gym", "period_year", "period_month", "billing_policy", "status", "item_count", "total_amount")
    list_filter = ("status", "billing_policy", "gym", "period_year")
    search_fields = ("invoice_number", "gym__name")
    readonly_fields = tuple(field.name for field in GymInvoice._meta.fields)
    inlines = (GymInvoiceItemInline,)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(GymInvoiceAuditLog)
class GymInvoiceAuditLogAdmin(admin.ModelAdmin):
    list_display = ("invoice", "action", "actor", "created_at")
    list_filter = ("action", "created_at")
    readonly_fields = tuple(field.name for field in GymInvoiceAuditLog._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
