from django.contrib import admin
from django.urls.base import reverse
from django.utils.safestring import mark_safe
from . import models
from anomalis.models import CorrectiveAction, Anomaly, AnomalyDescription, HSE, Comment, LocationSection
from .models import Location, Anomalytype, Priority
from .views import anomaly_list
import jdatetime

@admin.register(models.Anomaly)
class AnomalyAdmin(admin.ModelAdmin):
    list_display = ['id', 'location', 'anomalytype', 'priority', 'action', 'created_by', 'followup', 'created_at_jalali', 'updated_at_jalali']

    def created_at_jalali(self, obj):
        return jdatetime.datetime.fromgregorian(datetime=obj.created_at).strftime('%Y/%m/%d')
    created_at_jalali.short_description = 'تاریخ ایجاد (شمسی)'

    def updated_at_jalali(self, obj):
        return jdatetime.datetime.fromgregorian(datetime=obj.updated_at).strftime('%Y/%m/%d')
    updated_at_jalali.short_description = 'تاریخ بروزرسانی (شمسی)'


@admin.register(models.Comment)
class CommentInline(admin.ModelAdmin):
    list_display = ['id', 'user', 'get_anomaly_id', 'comment', 'created_at', 'updated_at']

    def get_anomaly_id(self, obj):
        url = reverse('anomalis:anomaly_detail', args=[obj.anomaly.id])
        return mark_safe(f'<a href="{url}">{obj.anomaly.id}</a>')

    get_anomaly_id.admin_order_field = 'anomaly__id'
    get_anomaly_id.short_description = 'نظر در این آنومالی'


admin.site.register(Location)
admin.site.register(LocationSection)
admin.site.register(Anomalytype)
admin.site.register(CorrectiveAction)
admin.site.register(Priority)
admin.site.register(AnomalyDescription)
admin.site.register(HSE)

