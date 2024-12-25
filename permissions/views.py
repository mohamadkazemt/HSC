from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden, JsonResponse
from .models import UnitPermission, DepartmentPermission, PositionPermission
from accounts.models import Unit, Department, Position
from .utils import get_all_views_with_labels, check_permission
from django.core.serializers.json import DjangoJSONEncoder
import json

def manage_access(request):
    """
    ویوی مدیریت دسترسی‌ها.
    """
    units = Unit.objects.values("id", "name")  # استخراج تمام واحدها
    departments = Department.objects.values("id", "name")  # استخراج تمام بخش‌ها
    positions = Position.objects.values("id", "name")  # استخراج تمام سمت‌ها
    views_with_labels = get_all_views_with_labels()  # دریافت ویوها همراه با لیبل‌ها
    print(views_with_labels)

    if request.method == "POST":
        entity_type = request.POST.get("entity_type")
        entity_id = request.POST.get("entity_id")
        view_names = request.POST.getlist("view_name")
        can_view = "can_view" in request.POST
        can_add = "can_add" in request.POST
        can_edit = "can_edit" in request.POST
        can_delete = "can_delete" in request.POST

        print("Entity Type:", entity_type)
        print("Entity ID:", entity_id)
        print("View Names:", view_names)
        print("Permissions:", can_view, can_add, can_edit, can_delete)

        for view_name in view_names:
            if entity_type == "unit":
                if not UnitPermission.objects.filter(unit_id=entity_id, view_name=view_name).exists():
                    UnitPermission.objects.create(
                        unit_id=entity_id,
                        view_name=view_name,
                        can_view=can_view,
                        can_add=can_add,
                        can_edit=can_edit,
                        can_delete=can_delete,
                    )
            elif entity_type == "department":
                if not DepartmentPermission.objects.filter(department_id=entity_id, view_name=view_name).exists():
                    DepartmentPermission.objects.create(
                        department_id=entity_id,
                        view_name=view_name,
                        can_view=can_view,
                        can_add=can_add,
                        can_edit=can_edit,
                        can_delete=can_delete,
                    )
            elif entity_type == "position":
                if not PositionPermission.objects.filter(position_id=entity_id, view_name=view_name).exists():
                    PositionPermission.objects.create(
                        position_id=entity_id,
                        view_name=view_name,
                        can_view=can_view,
                        can_add=can_add,
                        can_edit=can_edit,
                        can_delete=can_delete,
                    )

        return redirect("manage_access")

    return render(request, "permissions/manage_access.html", {
        "units": json.dumps(list(units), cls=DjangoJSONEncoder),
        "departments": json.dumps(list(departments), cls=DjangoJSONEncoder),
        "positions": json.dumps(list(positions), cls=DjangoJSONEncoder),
        "views_with_labels": views_with_labels,
    })

def validate_access(request, view_name):
    """
    ویوی بررسی دسترسی کاربر به ویوی مشخص.
    """
    if not check_permission(request.user, view_name):
        return HttpResponseForbidden("شما اجازه دسترسی به این بخش را ندارید.")
    return JsonResponse({"message": "دسترسی مجاز است"})

def list_permissions(request):
    """
    نمایش لیست دسترسی‌ها به صورت گرافیکی.
    """
    unit_permissions = UnitPermission.objects.all()
    department_permissions = DepartmentPermission.objects.all()
    position_permissions = PositionPermission.objects.all()

    return render(request, "permissions/list_permissions.html", {
        "unit_permissions": unit_permissions,
        "department_permissions": department_permissions,
        "position_permissions": position_permissions,
    })

def delete_permission(request, permission_type, permission_id):
    """
    حذف یک دسترسی خاص بر اساس نوع و ID.
    """
    if permission_type == "unit":
        permission = get_object_or_404(UnitPermission, id=permission_id)
    elif permission_type == "department":
        permission = get_object_or_404(DepartmentPermission, id=permission_id)
    elif permission_type == "position":
        permission = get_object_or_404(PositionPermission, id=permission_id)
    else:
        return HttpResponseForbidden("نوع دسترسی نامعتبر است.")

    permission.delete()
    return redirect("list_permissions")
