from django.contrib import admin
from .models import PartPermission, SectionPermission, PositionPermission ,UnitGroupPermission, UserPermission
from .utils import get_all_views_with_labels  # Import the function to get views with labels dynamically

@admin.register(PartPermission)
class PartPermissionAdmin(admin.ModelAdmin):
    list_display = ('part', 'view_name', 'can_view', 'can_add', 'can_edit', 'can_delete')

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "view_name":
            views_with_labels = get_all_views_with_labels()
            print("Admin Choices for View Names:", views_with_labels)  # چاپ داده‌ها برای بررسی
            kwargs['choices'] = [(view['name'], view['label']) for view in views_with_labels]
        return super().formfield_for_choice_field(db_field, request, **kwargs)


@admin.register(SectionPermission)
class SectionPermissionAdmin(admin.ModelAdmin):
    list_display = ('section', 'view_name', 'can_view', 'can_add', 'can_edit', 'can_delete')

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "view_name":
            views_with_labels = get_all_views_with_labels()
            print("Admin Choices for View Names:", views_with_labels)  # چاپ داده‌ها برای بررسی
            kwargs['choices'] = [(view['name'], view['label']) for view in views_with_labels]
        return super().formfield_for_choice_field(db_field, request, **kwargs)


@admin.register(PositionPermission)
class PositionPermissionAdmin(admin.ModelAdmin):
    list_display = ('position', 'view_name', 'can_view', 'can_add', 'can_edit', 'can_delete')

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "view_name":
            views_with_labels = get_all_views_with_labels()
            print("Admin Choices for View Names:", views_with_labels)  # چاپ داده‌ها برای بررسی
            kwargs['choices'] = [(view['name'], view['label']) for view in views_with_labels]
        return super().formfield_for_choice_field(db_field, request, **kwargs)


@admin.register(UnitGroupPermission)
class UnitGroupPermissionAdmin(admin.ModelAdmin):
    list_display = ('unit_group', 'view_name', 'can_view', 'can_add', 'can_edit', 'can_delete')

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "view_name":
            views_with_labels = get_all_views_with_labels()
            print("Admin Choices for View Names:", views_with_labels)  # چاپ داده‌ها برای بررسی
            kwargs['choices'] = [(view['name'], view['label']) for view in views_with_labels]
        return super().formfield_for_choice_field(db_field, request, **kwargs)

@admin.register(UserPermission)
class UserPermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'view_name', 'can_view', 'can_add', 'can_edit', 'can_delete')

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "view_name":
            views_with_labels = get_all_views_with_labels()
            print("Admin Choices for View Names:", views_with_labels)  # چاپ داده‌ها برای بررسی
            kwargs['choices'] = [(view['name'], view['label']) for view in views_with_labels]
        return super().formfield_for_choice_field(db_field, request, **kwargs)