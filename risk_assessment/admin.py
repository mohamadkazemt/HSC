from django.contrib import admin
from django.utils.html import format_html
from .models import RiskAssessment, JobTask, RiskAssessmentHistory


@admin.register(JobTask)
class JobTaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'position', 'name', 'is_active', 'order']
    list_filter = ['position', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['position', 'order']


@admin.register(RiskAssessment)
class RiskAssessmentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'position',
        'activity_component',
        'hazard',
        'risk_number_colored',
        'risk_level_badge',
        'residual_risk_number_colored',
        'corrective_action_required',
        'created_at',
    ]
    
    list_filter = [
        'risk_level',
        'position',
        'risk_source',
        'is_routine',
        'corrective_action_required',
        'is_mue',
        'is_emergency',
        'has_legal_requirement',
        'created_at',
    ]
    
    search_fields = [
        'activity_component',
        'potential_event',
        'causes',
        'action_number',
        'mue_code',
        'emergency_code',
    ]
    
    readonly_fields = [
        'risk_number',
        'risk_level',
        'residual_risk_number',
        'residual_risk_level',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('اطلاعات شغل و منشا', {
            'fields': (
                'position',
                'risk_source',
                'risk_source_other',
            )
        }),
        ('مشخصات فعالیت', {
            'fields': (
                'activity_component',
                'is_routine',
            )
        }),
        ('شناسایی خطر', {
            'fields': (
                'hazard',
                'people_at_risk',
                'potential_event',
                'causes',
                'consequence',
            )
        }),
        ('کنترل‌های موجود', {
            'fields': (
                'existing_controls',
                'control_failure_causes',
            )
        }),
        ('الزامات قانونی', {
            'fields': (
                'has_legal_requirement',
                'legal_requirement_desc',
                'is_legal_compliant',
            ),
            'classes': ('collapse',),
        }),
        ('ارزیابی ریسک اولیه', {
            'fields': (
                'probability',
                'severity',
                'risk_number',
                'risk_level',
            )
        }),
        ('کنترل‌های پیشنهادی (Hierarchy)', {
            'fields': (
                'control_elimination',
                'control_substitution',
                'control_engineering',
                'control_admin',
                'control_ppe',
            ),
            'classes': ('collapse',),
        }),
        ('اقدامات اصلاحی', {
            'fields': (
                'corrective_action_required',
                'action_number',
                'action_date',
                'action_deadline',
                'responsible_person',
            )
        }),
        ('MUE و شرایط اضطراری', {
            'fields': (
                'is_mue',
                'mue_code',
                'is_emergency',
                'emergency_code',
            ),
            'classes': ('collapse',),
        }),
        ('ارزیابی مجدد', {
            'fields': (
                're_evaluation_date',
                'residual_probability',
                'residual_severity',
                'residual_risk_number',
                'residual_risk_level',
            ),
            'classes': ('collapse',),
        }),
        ('سایر اطلاعات', {
            'fields': (
                'notes',
                'created_by',
                'created_at',
                'updated_at',
            )
        }),
    )
    
    filter_horizontal = ['people_at_risk']

    def get_inlines(self, request, obj=None):
        return [RiskHistoryInline]

    # ======= Custom colored columns for list_display =======
    def _get_bg_color(self, color_name):
        colors = {
            'success': '#28a745',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'secondary': '#6c757d',
        }
        return colors.get(color_name, '#6c757d')

    def risk_number_colored(self, obj):
        color = obj.get_risk_color()
        return format_html(
            '<span style="background-color:{};color:#fff;padding:4px 8px;border-radius:4px;font-weight:600;display:inline-block;min-width:46px;text-align:center;">{}</span>',
            self._get_bg_color(color),
            obj.risk_number
        )
    risk_number_colored.short_description = 'عدد ریسک'
    risk_number_colored.admin_order_field = 'risk_number'

    def risk_level_badge(self, obj):
        color = obj.get_risk_color()
        return format_html(
            '<span style="background-color:{};color:#fff;padding:4px 10px;border-radius:12px;font-size:11px;">{}</span>',
            self._get_bg_color(color),
            obj.get_risk_level_display_fa()
        )
    risk_level_badge.short_description = 'سطح'
    risk_level_badge.admin_order_field = 'risk_level'

    def residual_risk_number_colored(self, obj):
        if not obj.residual_risk_number:
            return '-'
        color = obj.get_residual_risk_color()
        return format_html(
            '<span style="background-color:{};color:#fff;padding:4px 8px;border-radius:4px;font-weight:600;display:inline-block;min-width:46px;text-align:center;">{}</span>',
            self._get_bg_color(color),
            obj.residual_risk_number
        )
    residual_risk_number_colored.short_description = 'ریسک باقی'
    residual_risk_number_colored.admin_order_field = 'residual_risk_number'


class RiskHistoryInline(admin.TabularInline):
    model = RiskAssessmentHistory
    extra = 0
    readonly_fields = [
        'change_type','probability','severity','risk_number','risk_level',
        'residual_probability','residual_severity','residual_risk_number','residual_risk_level','created_at'
    ]
    can_delete = False
    
    def risk_number_colored(self, obj):
        """نمایش عدد ریسک با رنگ"""
        # History شیء متد get_risk_color ندارد؛ بر اساس risk_level نقشه می‌کنیم
        color_map = {'Low': 'success', 'Medium': 'warning', 'High': 'danger'}
        color = color_map.get(obj.risk_level, 'secondary')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            self._get_bg_color(color),
            obj.risk_number
        )
    risk_number_colored.short_description = 'عدد ریسک (RPN)'
    
    def risk_level_badge(self, obj):
        """نمایش سطح ریسک به صورت badge"""
        color_map = {'Low': 'success', 'Medium': 'warning', 'High': 'danger'}
        label_map = {'Low': 'پایین', 'Medium': 'متوسط', 'High': 'بالا'}
        color = color_map.get(obj.risk_level, 'secondary')
        label = label_map.get(obj.risk_level, '-')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px;">{}</span>',
            self._get_bg_color(color),
            label
        )
    risk_level_badge.short_description = 'سطح ریسک'
    
    def residual_risk_number_colored(self, obj):
        """نمایش عدد ریسک باقی‌مانده با رنگ"""
        if obj.residual_risk_number:
            color_map = {'Low': 'success', 'Medium': 'warning', 'High': 'danger'}
            color = color_map.get(obj.residual_risk_level, 'secondary')
            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
                self._get_bg_color(color),
                obj.residual_risk_number
            )
        return '-'
    residual_risk_number_colored.short_description = 'ریسک باقی‌مانده'
    
    def _get_bg_color(self, color_name):
        """تبدیل نام رنگ Bootstrap به کد رنگ"""
        colors = {
            'success': '#28a745',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'secondary': '#6c757d',
        }
        return colors.get(color_name, '#6c757d')
    
    def save_model(self, request, obj, form, change):
        """ذخیره اطلاعات ایجادکننده"""
        if not change and hasattr(request.user, 'userprofile'):
            obj.created_by = request.user.userprofile
        super().save_model(request, obj, form, change)
