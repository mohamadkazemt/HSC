from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .models import ModuleSetting, SiteSettings
from .module_registry import MODULES, get_module_title
from .ai_models import AISettings

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    pass

@admin.register(AISettings)
class AISettingsAdmin(admin.ModelAdmin):
    list_display = ['provider', 'model', 'is_active', 'last_test_status', 'last_tested_at', 'updated_at']
    readonly_fields = ['last_tested_at', 'last_test_status', 'last_test_message', 'updated_at']
    fieldsets = (
        ('تنظیمات اصلی', {
            'fields': ('provider', 'api_key', 'api_base_url', 'model', 'is_active')
        }),
        ('تنظیمات پیشرفته', {
            'fields': ('timeout', 'max_retries', 'cache_timeout', 'temperature'),
            'classes': ('collapse',)
        }),
        ('اطلاعات تست', {
            'fields': ('last_tested_at', 'last_test_status', 'last_test_message'),
            'classes': ('collapse',)
        }),
        ('سایر', {
            'fields': ('updated_at',)
        }),
    )


class ModuleSettingAdminForm(forms.ModelForm):
    activation_password = forms.CharField(
        label="رمز عبور مدیر برای فعال‌سازی",
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="فقط هنگام تغییر وضعیت از غیرفعال به فعال، رمز حساب فعلی را وارد کنید.",
    )

    class Meta:
        model = ModuleSetting
        fields = "__all__"

    def clean_module_key(self):
        module_key = self.cleaned_data["module_key"]
        if module_key not in MODULES:
            raise ValidationError("این ماژول قابل مدیریت نیست.")
        return module_key

    def clean(self):
        cleaned_data = super().clean()
        was_active = self.instance.is_active if self.instance.pk else False
        will_be_active = cleaned_data.get("is_active", False)
        if not was_active and will_be_active:
            password = cleaned_data.get("activation_password")
            request = getattr(self, "request", None)
            if not password or request is None or not request.user.check_password(password):
                self.add_error("activation_password", "رمز عبور حساب مدیر صحیح نیست.")
        return cleaned_data


@admin.register(ModuleSetting)
class ModuleSettingAdmin(admin.ModelAdmin):
    form = ModuleSettingAdminForm
    list_display = ("module_title", "status_toggle", "modified_by", "modified_at")
    list_editable = ()
    list_filter = ("is_active",)
    readonly_fields = ("module_key", "modified_by", "modified_at")
    actions = None

    @admin.display(description="ماژول", ordering="module_key")
    def module_title(self, obj):
        return get_module_title(obj.module_key)

    @admin.display(description="فعال / غیرفعال", ordering="is_active")
    def status_toggle(self, obj):
        toggle_url = reverse("admin:core_modulesetting_toggle", args=(obj.pk,))
        return format_html(
            '<input type="checkbox" class="module-status-toggle" '
            'data-toggle-url="{}" data-module-title="{}" {} '
            'aria-label="تغییر وضعیت {}">',
            toggle_url,
            get_module_title(obj.module_key),
            "checked" if obj.is_active else "",
            get_module_title(obj.module_key),
        )

    def get_urls(self):
        custom_urls = [
            path(
                "<int:object_id>/toggle/",
                self.admin_site.admin_view(self.toggle_module),
                name="core_modulesetting_toggle",
            ),
        ]
        return custom_urls + super().get_urls()

    def toggle_module(self, request, object_id):
        if request.method != "POST":
            return JsonResponse({"ok": False, "message": "درخواست نامعتبر است."}, status=405)

        if not self.has_change_permission(request):
            return JsonResponse({"ok": False, "message": "اجازه تغییر ماژول را ندارید."}, status=403)

        try:
            module = ModuleSetting.objects.get(pk=object_id)
        except ModuleSetting.DoesNotExist:
            return JsonResponse({"ok": False, "message": "ماژول پیدا نشد."}, status=404)

        requested_active = request.POST.get("is_active") == "true"
        if requested_active and not module.is_active:
            password = request.POST.get("activation_password", "")
            if not password or not request.user.check_password(password):
                return JsonResponse(
                    {"ok": False, "message": "رمز عبور حساب مدیر صحیح نیست."},
                    status=400,
                )

        module.is_active = requested_active
        module.modified_by = request.user
        module.save(update_fields=("is_active", "modified_by", "modified_at"))
        return JsonResponse({"ok": True, "is_active": module.is_active})

    def get_form(self, request, obj=None, **kwargs):
        form_class = super().get_form(request, obj, **kwargs)
        form_class.request = request
        return form_class

    def save_model(self, request, obj, form, change):
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    class Media:
        js = ("core/js/module_toggle.js",)
