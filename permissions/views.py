from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden, JsonResponse
from .models import UnitPermission, DepartmentPermission, PositionPermission
from accounts.models import Unit, Department, Position
from .utils import get_all_views_with_labels, check_permission
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.db.models import Q
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages





@user_passes_test(lambda user: user.is_superuser)
def manage_access(request):
    """
    ویوی مدیریت دسترسی‌ها.
    """
    units = Unit.objects.values("id", "name")  # استخراج تمام واحدها
    departments = Department.objects.values("id", "name")  # استخراج تمام بخش‌ها
    positions = Position.objects.values("id", "name")  # استخراج تمام سمت‌ها
    views_with_labels = get_all_views_with_labels()  # دریافت ویوها همراه با لیبل‌ها

    if request.method == "POST":
        entity_type = request.POST.get("entity_type")
        entity_id = request.POST.get("entity_id")
        view_names = request.POST.getlist("view_name")
        can_view = "can_view" in request.POST
        can_add = "can_add" in request.POST
        can_edit = "can_edit" in request.POST
        can_delete = "can_delete" in request.POST

        for view_name in view_names:
            if entity_type == "unit":
                # بررسی وجود رکورد
                if UnitPermission.objects.filter(unit_id=entity_id, view_name=view_name).exists():
                    messages.warning(request, f"رکورد برای واحد {entity_id} و ویو {view_name} قبلاً ثبت شده است.")
                    continue
                UnitPermission.objects.create(
                    unit_id=entity_id,
                    view_name=view_name,
                    can_view=can_view,
                    can_add=can_add,
                    can_edit=can_edit,
                    can_delete=can_delete,
                )
            elif entity_type == "department":
                # بررسی وجود رکورد
                if DepartmentPermission.objects.filter(department_id=entity_id, view_name=view_name).exists():
                    messages.warning(request, f"رکورد برای بخش {entity_id} و ویو {view_name} قبلاً ثبت شده است.")
                    continue
                DepartmentPermission.objects.create(
                    department_id=entity_id,
                    view_name=view_name,
                    can_view=can_view,
                    can_add=can_add,
                    can_edit=can_edit,
                    can_delete=can_delete,
                )
            elif entity_type == "position":
                # بررسی وجود رکورد
                if PositionPermission.objects.filter(position_id=entity_id, view_name=view_name).exists():
                    messages.warning(request, f"رکورد برای پست {entity_id} و ویو {view_name} قبلاً ثبت شده است.")
                    continue
                PositionPermission.objects.create(
                    position_id=entity_id,
                    view_name=view_name,
                    can_view=can_view,
                    can_add=can_add,
                    can_edit=can_edit,
                    can_delete=can_delete,
                )

        messages.success(request, "دسترسی‌ها با موفقیت به‌روزرسانی شدند.")
        return redirect("permissions:manage_access")

    return render(request, "permissions/manage_access.html", {
        "units": json.dumps(list(units), cls=DjangoJSONEncoder),
        "departments": json.dumps(list(departments), cls=DjangoJSONEncoder),
        "positions": json.dumps(list(positions), cls=DjangoJSONEncoder),
        "views_with_labels": views_with_labels,
    })




@user_passes_test(lambda user: user.is_superuser)
def validate_access(request, view_name):
    """
    ویوی بررسی دسترسی کاربر به ویوی مشخص.
    """
    if not check_permission(request.user, view_name):
        return HttpResponseForbidden("شما اجازه دسترسی به این بخش را ندارید.")
    return JsonResponse({"message": "دسترسی مجاز است"})


@user_passes_test(lambda user: user.is_superuser)

def list_permissions(request):
    # فیلترها
    unit_filter = request.GET.get('unit')
    department_filter = request.GET.get('department')
    position_filter = request.GET.get('position')

    # داده‌ها
    units = Unit.objects.all()
    departments = Department.objects.all()
    positions = Position.objects.all()

    # جمع‌آوری دسترسی‌ها
    permissions = []

    if unit_filter:
        unit_permissions = UnitPermission.objects.filter(unit_id=unit_filter)
        for permission in unit_permissions:
            permissions.append({
                'type': 'واحد',
                'name': permission.unit.name,
                'view_name': permission.view_name,
                'can_view': permission.can_view,
                'can_add': permission.can_add,
                'can_edit': permission.can_edit,
                'can_delete': permission.can_delete,
                'id': permission.id
            })

    if department_filter:
        department_permissions = DepartmentPermission.objects.filter(department_id=department_filter)
        for permission in department_permissions:
            permissions.append({
                'type': 'بخش',
                'name': permission.department.name,
                'view_name': permission.view_name,
                'can_view': permission.can_view,
                'can_add': permission.can_add,
                'can_edit': permission.can_edit,
                'can_delete': permission.can_delete,
                'id': permission.id
            })

    if position_filter:
        position_permissions = PositionPermission.objects.filter(position_id=position_filter)
        for permission in position_permissions:
            permissions.append({
                'type': 'پست',
                'name': permission.position.name,
                'view_name': permission.view_name,
                'can_view': permission.can_view,
                'can_add': permission.can_add,
                'can_edit': permission.can_edit,
                'can_delete': permission.can_delete,
                'id': permission.id
            })

    if not unit_filter and not department_filter and not position_filter:
        # بدون فیلتر همه موارد را نمایش بده
        unit_permissions = UnitPermission.objects.all()
        department_permissions = DepartmentPermission.objects.all()
        position_permissions = PositionPermission.objects.all()

        for permission in unit_permissions:
            permissions.append({
                'type': 'واحد',
                'name': permission.unit.name,
                'view_name': permission.view_name,
                'can_view': permission.can_view,
                'can_add': permission.can_add,
                'can_edit': permission.can_edit,
                'can_delete': permission.can_delete,
                'id': permission.id
            })

        for permission in department_permissions:
            permissions.append({
                'type': 'بخش',
                'name': permission.department.name,
                'view_name': permission.view_name,
                'can_view': permission.can_view,
                'can_add': permission.can_add,
                'can_edit': permission.can_edit,
                'can_delete': permission.can_delete,
                'id': permission.id
            })

        for permission in position_permissions:
            permissions.append({
                'type': 'پست',
                'name': permission.position.name,
                'view_name': permission.view_name,
                'can_view': permission.can_view,
                'can_add': permission.can_add,
                'can_edit': permission.can_edit,
                'can_delete': permission.can_delete,
                'id': permission.id
            })

    context = {
        'permissions': permissions,
        'units': units,
        'departments': departments,
        'positions': positions,
    }

    return render(request, 'permissions/list_permissions.html', context)


@user_passes_test(lambda user: user.is_superuser)

def edit_permission(request, permission_id):
    permission_type = request.GET.get('type')  # دریافت نوع دسترسی از پارامتر GET
    permission = None

    # بررسی نوع دسترسی و بازیابی داده
    if permission_type == 'واحد':
        permission = get_object_or_404(UnitPermission, id=permission_id)
    elif permission_type == 'بخش':
        permission = get_object_or_404(DepartmentPermission, id=permission_id)
    elif permission_type == 'پست':
        permission = get_object_or_404(PositionPermission, id=permission_id)
    else:
        return HttpResponseForbidden("نوع دسترسی نامعتبر است.")

    if request.method == 'POST':
        # دریافت اطلاعات از فرم
        can_view = request.POST.get('can_view') == 'on'
        can_add = request.POST.get('can_add') == 'on'
        can_edit = request.POST.get('can_edit') == 'on'
        can_delete = request.POST.get('can_delete') == 'on'

        # به‌روزرسانی اطلاعات
        permission.can_view = can_view
        permission.can_add = can_add
        permission.can_edit = can_edit
        permission.can_delete = can_delete
        permission.save()

        return redirect('permissions:list_permissions')

    # ارسال اطلاعات به قالب
    return render(request, 'permissions/edit_permission.html', {
        'permission': permission,
        'permission_type': permission_type  # ارسال نوع دسترسی به قالب
    })



@user_passes_test(lambda user: user.is_superuser)

def delete_permission(request, permission_id):
    permission_type = request.GET.get('type')  # نوع دسترسی

    if permission_type == 'واحد':
        permission = get_object_or_404(UnitPermission, id=permission_id)
    elif permission_type == 'بخش':
        permission = get_object_or_404(DepartmentPermission, id=permission_id)
    elif permission_type == 'پست':
        permission = get_object_or_404(PositionPermission, id=permission_id)
    else:
        return HttpResponseForbidden("نوع دسترسی نامعتبر است.")

    permission.delete()
    return redirect('permissions:list_permissions')
