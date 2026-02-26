from django.contrib import admin

from .models import (
    DumpCountEvent,
    DumpCountSession,
    LoadingHaulingReport,
    MachineActivity,
)


@admin.register(MachineActivity)
class MachineActivityAdmin(admin.ModelAdmin):
    list_display = ('machine', 'date', 'shift', 'operator_name', 'work_hours', 'ready_hours', 'stop_hours')
    list_filter = ('date', 'shift', 'stop_reason')
    search_fields = ('machine__workshop_code', 'operator_name')


@admin.register(LoadingHaulingReport)
class LoadingHaulingReportAdmin(admin.ModelAdmin):
    list_display = ('date', 'shift', 'loader_machine', 'dumper_machine', 'material_type', 'block', 'dump', 'service_count')
    list_filter = ('date', 'shift', 'material_type')
    search_fields = ('loader_machine__workshop_code', 'dumper_machine__workshop_code', 'block__block_name', 'dump__dump_name')


@admin.register(DumpCountSession)
class DumpCountSessionAdmin(admin.ModelAdmin):
    list_display = ('date', 'shift', 'block', 'dump', 'loader_machine', 'counter_name', 'start_time', 'end_time')
    list_filter = ('date', 'shift')
    search_fields = ('block__block_name', 'dump__dump_name', 'loader_machine__workshop_code', 'counter_name', 'loader_operator_name')


@admin.register(DumpCountEvent)
class DumpCountEventAdmin(admin.ModelAdmin):
    list_display = ('session', 'load_time', 'dumper_machine', 'driver_name')
    list_filter = ('load_time',)
    search_fields = ('driver_name', 'session__block__block_name')
