from django.contrib import admin
from .models import UnitPermission, DepartmentPermission, PositionPermission

@admin.register(UnitPermission)
class UnitPermissionAdmin(admin.ModelAdmin):
    list_display = ('unit', 'view_name', 'can_view', 'can_add', 'can_edit', 'can_delete')

@admin.register(DepartmentPermission)
class DepartmentPermissionAdmin(admin.ModelAdmin):
    list_display = ('department', 'view_name', 'can_view', 'can_add', 'can_edit', 'can_delete')

@admin.register(PositionPermission)
class PositionPermissionAdmin(admin.ModelAdmin):
    list_display = ('position', 'view_name', 'can_view', 'can_add', 'can_edit', 'can_delete')
