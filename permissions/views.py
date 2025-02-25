from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden, JsonResponse
from .models import PartPermission, SectionPermission, PositionPermission ,UnitGroupPermission, UserPermission
from accounts.models import Part, Section, Position,UnitGroup
from .utils import get_all_views_with_labels, check_permission
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.db.models import Q
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from dashboard.utils import log_user_activity
from django.urls import reverse



@user_passes_test(lambda user: user.is_superuser)
def manage_access(request):
    """
    ویوی مدیریت دسترسی‌ها.
    """
    # ثبت فعالیت مشاهده صفحه مدیریت دسترسی‌ها
    if request.method == "GET":
        log_user_activity(
            user=request.user,
            activity_type='view',
            description='مشاهده صفحه مدیریت دسترسی‌ها',
            related_model='Permission',
            related_object_id=None,
            url=reverse('permissions:manage_access'),
            request=request
        )
    
    parts = Part.objects.values("id", "name")  # استخراج تمام قسمت‌ها
    sections = Section.objects.values("id", "name")  # استخراج تمام بخش‌ها
    positions = Position.objects.values("id", "name")  # استخراج تمام سمت‌ها
    unit_groups = UnitGroup.objects.values("id", "name")  # استخراج تمام گروه ها

    users = []
    for user in User.objects.all():
        user_profile = getattr(user, 'userprofile', None)
        if user_profile:
            users.append({"id": user.id, "name": f"{user.first_name} {user.last_name} ({user_profile.personnel_code})"})
        else:
            users.append({"id": user.id, "name": f"{user.first_name} {user.last_name}"})

    views_with_labels = get_all_views_with_labels()  # دریافت ویوها همراه با لیبل‌ها

    if request.method == "POST":
        entity_type = request.POST.get("entity_type")
        entity_id = request.POST.get("entity_id")
        view_names = request.POST.getlist("view_name")
        can_view = "can_view" in request.POST
        can_add = "can_add" in request.POST
        can_edit = "can_edit" in request.POST
        can_delete = "can_delete" in request.POST
        
        # ثبت فعالیت ایجاد دسترسی جدید
        entity_name = ""
        if entity_type == "part":
            part = Part.objects.get(id=entity_id)
            entity_name = f"قسمت {part.name}"
        elif entity_type == "section":
            section = Section.objects.get(id=entity_id)
            entity_name = f"بخش {section.name}"
        elif entity_type == "position":
            position = Position.objects.get(id=entity_id)
            entity_name = f"سمت {position.name}"
        elif entity_type == "unit_group":
            unit_group = UnitGroup.objects.get(id=entity_id)
            entity_name = f"گروه {unit_group.name}"
        elif entity_type == "user":
            user = User.objects.get(id=entity_id)
            entity_name = f"کاربر {user.first_name} {user.last_name}"
        
        log_user_activity(
            user=request.user,
            activity_type='create',
            description=f'ایجاد دسترسی جدید برای {entity_name}',
            related_model='Permission',
            related_object_id=None,
            url=reverse('permissions:manage_access'),
            request=request
        )

        for view_name in view_names:
            if entity_type == "part":
                # بررسی وجود رکورد
                if PartPermission.objects.filter(part_id=entity_id, view_name=view_name).exists():
                    messages.warning(request, f"رکورد برای قسمت {entity_id} و ویو {view_name} قبلاً ثبت شده است.")
                    continue
                PartPermission.objects.create(
                    part_id=entity_id,
                    view_name=view_name,
                    can_view=can_view,
                    can_add=can_add,
                    can_edit=can_edit,
                    can_delete=can_delete,
                )
            elif entity_type == "section":
                # بررسی وجود رکورد
                if SectionPermission.objects.filter(section_id=entity_id, view_name=view_name).exists():
                    messages.warning(request, f"رکورد برای بخش {entity_id} و ویو {view_name} قبلاً ثبت شده است.")
                    continue
                SectionPermission.objects.create(
                    section_id=entity_id,
                    view_name=view_name,
                    can_view=can_view,
                    can_add=can_add,
                    can_edit=can_edit,
                    can_delete=can_delete,
                )
            elif entity_type == "unit_group":
                # بررسی وجود رکورد
                if UnitGroupPermission.objects.filter(unit_group_id=entity_id, view_name=view_name).exists():
                    messages.warning(request, f"رکورد برای گروه {entity_id} و ویو {view_name} قبلاً ثبت شده است.")
                    continue
                UnitGroupPermission.objects.create(
                    unit_group_id=entity_id,
                    view_name=view_name,
                    can_view=can_view,
                    can_add=can_add,
                    can_edit=can_edit,
                    can_delete=can_delete,
                )
            elif entity_type == "position":
                # بررسی وجود رکورد
                if PositionPermission.objects.filter(position_id=entity_id, view_name=view_name).exists():
                    messages.warning(request, f"رکورد برای سمت {entity_id} و ویو {view_name} قبلاً ثبت شده است.")
                    continue
                PositionPermission.objects.create(
                    position_id=entity_id,
                    view_name=view_name,
                    can_view=can_view,
                    can_add=can_add,
                    can_edit=can_edit,
                    can_delete=can_delete,
                )
            elif entity_type == "user":
                # بررسی وجود رکورد
                if UserPermission.objects.filter(user_id=entity_id, view_name=view_name).exists():
                    messages.warning(request, f"رکورد برای کاربر {entity_id} و ویو {view_name} قبلاً ثبت شده است.")
                    continue
                UserPermission.objects.create(
                    user_id=entity_id,
                    view_name=view_name,
                    can_view=can_view,
                    can_add=can_add,
                    can_edit=can_edit,
                    can_delete=can_delete,
                )

        messages.success(request, "دسترسی‌ها با موفقیت به‌روزرسانی شدند.")
        return redirect("permissions:manage_access")

    return render(request, "permissions/manage_access.html", {
        "parts": json.dumps(list(parts), cls=DjangoJSONEncoder),
        "sections": json.dumps(list(sections), cls=DjangoJSONEncoder),
        "positions": json.dumps(list(positions), cls=DjangoJSONEncoder),
        "unit_groups": json.dumps(list(unit_groups), cls=DjangoJSONEncoder),
        "users": json.dumps(list(users), cls=DjangoJSONEncoder),
        "views_with_labels": views_with_labels,
    })


@user_passes_test(lambda user: user.is_superuser)
def validate_access(request, view_name):
    """
    ویوی بررسی دسترسی کاربر به ویوی مشخص.
    """
    # ثبت فعالیت بررسی دسترسی
    log_user_activity(
        user=request.user,
        activity_type='view',
        description=f'بررسی دسترسی به ویو {view_name}',
        related_model='Permission',
        related_object_id=None,
        url=request.path,
        request=request
    )
    
    if not check_permission(request.user, view_name):
        return HttpResponseForbidden("شما اجازه دسترسی به این بخش را ندارید.")
    return JsonResponse({"message": "دسترسی مجاز است"})


@user_passes_test(lambda user: user.is_superuser)
def list_permissions(request):
    # ثبت فعالیت مشاهده لیست دسترسی‌ها
    log_user_activity(
        user=request.user,
        activity_type='view',
        description='مشاهده لیست دسترسی‌ها',
        related_model='Permission',
        related_object_id=None,
        url=reverse('permissions:list_permissions'),
        request=request
    )
    
    # فیلترها
    part_filter = request.GET.get('part')
    section_filter = request.GET.get('section')
    position_filter = request.GET.get('position')
    unit_group_filter = request.GET.get('unit_group')
    user_filter = request.GET.get('user')

    # داده‌ها
    parts = Part.objects.all()
    sections = Section.objects.all()
    positions = Position.objects.all()
    unit_groups=UnitGroup.objects.all()
    users = User.objects.all()

    # دریافت لیبل‌ها
    views_with_labels = get_all_views_with_labels()
    view_labels = {view['name']: view['label'] for view in views_with_labels}

    permissions = []

    def add_permission(permission, entity_type, entity_name):
        permissions.append({
            'type': entity_type,
            'name': entity_name,
            'view_name': permission.view_name,
            'view_label': view_labels.get(permission.view_name, permission.view_name),
            # نمایش نام ویو در صورت عدم وجود لیبل
            'can_view': permission.can_view,
            'can_add': permission.can_add,
            'can_edit': permission.can_edit,
            'can_delete': permission.can_delete,
            'id': permission.id
        })

    if part_filter:
        part_permissions = PartPermission.objects.filter(part_id=part_filter)
        for permission in part_permissions:
            add_permission(permission, 'قسمت', permission.part.name)

    if section_filter:
        section_permissions = SectionPermission.objects.filter(section_id=section_filter)
        for permission in section_permissions:
            add_permission(permission, 'بخش', permission.section.name)

    if position_filter:
        position_permissions = PositionPermission.objects.filter(position_id=position_filter)
        for permission in position_permissions:
            add_permission(permission, 'سمت', permission.position.name)

    if unit_group_filter:
        unit_group_permissions = UnitGroupPermission.objects.filter(unit_group_id=unit_group_filter)
        for permission in unit_group_permissions:
            add_permission(permission, 'گروه', permission.unit_group.name)

    if user_filter:
        user_permissions = UserPermission.objects.filter(user_id=user_filter)
        for permission in user_permissions:
            user_profile = getattr(permission.user, 'userprofile', None)  # تلاش برای دریافت UserProfile

            if user_profile:
                entity_name = f"{permission.user.first_name} {permission.user.last_name} ({user_profile.personnel_code})"
            else:
                entity_name = f"{permission.user.first_name} {permission.user.last_name}"

            add_permission(permission, 'کاربر', entity_name)

    if not part_filter and not section_filter and not position_filter and not unit_group_filter and not user_filter:
        # بدون فیلتر همه موارد را نمایش بده
        part_permissions = PartPermission.objects.all()
        section_permissions = SectionPermission.objects.all()
        position_permissions = PositionPermission.objects.all()
        unit_group_permissions = UnitGroupPermission.objects.all()
        user_permissions = UserPermission.objects.all()

        for permission in part_permissions:
            add_permission(permission, 'قسمت', permission.part.name)

        for permission in section_permissions:
            add_permission(permission, 'بخش', permission.section.name)

        for permission in position_permissions:
            add_permission(permission, 'سمت', permission.position.name)

        for permission in unit_group_permissions:
            add_permission(permission, 'گروه', permission.unit_group.name)

        for permission in user_permissions:
            user_profile = getattr(permission.user, 'userprofile', None)  # تلاش برای دریافت UserProfile

            if user_profile:
                entity_name = f"{permission.user.first_name} {permission.user.last_name} ({user_profile.personnel_code})"
            else:
                entity_name = f"{permission.user.first_name} {permission.user.last_name}"

            add_permission(permission, 'کاربر', entity_name)

    context = {
        'permissions': permissions,
        'parts': parts,
        'sections': sections,
        'positions': positions,
        'unit_groups': unit_groups,
        'users': users,
    }

    return render(request, 'permissions/list_permissions.html', context)


@user_passes_test(lambda user: user.is_superuser)
def edit_permission(request, permission_id):
    permission_type = request.GET.get('type')  # دریافت نوع دسترسی از پارامتر GET
    permission = None

    # بررسی نوع دسترسی و بازیابی داده
    if permission_type == 'قسمت':
        permission = get_object_or_404(PartPermission, id=permission_id)
    elif permission_type == 'بخش':
        permission = get_object_or_404(SectionPermission, id=permission_id)
    elif permission_type == 'سمت':
        permission = get_object_or_404(PositionPermission, id=permission_id)
    elif permission_type == 'گروه':
        permission = get_object_or_404(UnitGroupPermission, id=permission_id)
    elif permission_type == 'کاربر':
        permission = get_object_or_404(UserPermission, id=permission_id)
    else:
        return HttpResponseForbidden("نوع دسترسی نامعتبر است.")
    
    # ثبت فعالیت مشاهده فرم ویرایش دسترسی
    if request.method == 'GET':
        log_user_activity(
            user=request.user,
            activity_type='view',
            description=f'مشاهده فرم ویرایش دسترسی {permission_id}',
            related_model='Permission',
            related_object_id=permission_id,
            url=request.path,
            request=request
        )

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
        
        # ثبت فعالیت ویرایش دسترسی
        log_user_activity(
            user=request.user,
            activity_type='update',
            description=f'ویرایش دسترسی {permission_id}',
            related_model='Permission',
            related_object_id=permission_id,
            url=reverse('permissions:list_permissions'),
            request=request
        )

        messages.success(request, "دسترسی با موفقیت به‌روزرسانی شد.")
        return redirect('permissions:list_permissions')

    # دریافت لیبل ویو
    views_with_labels = get_all_views_with_labels()
    view_label = permission.view_name
    for view in views_with_labels:
        if view['name'] == permission.view_name:
            view_label = view['label']
            break

    context = {
        'permission': permission,
        'permission_type': permission_type,
        'view_label': view_label,
    }
    return render(request, 'permissions/edit_permission.html', context)


@user_passes_test(lambda user: user.is_superuser)
def delete_permission(request, permission_id):
    permission_type = request.GET.get('type')  # دریافت نوع دسترسی از پارامتر GET
    permission = None

    # بررسی نوع دسترسی و بازیابی داده
    if permission_type == 'قسمت':
        permission = get_object_or_404(PartPermission, id=permission_id)
    elif permission_type == 'بخش':
        permission = get_object_or_404(SectionPermission, id=permission_id)
    elif permission_type == 'سمت':
        permission = get_object_or_404(PositionPermission, id=permission_id)
    elif permission_type == 'گروه':
        permission = get_object_or_404(UnitGroupPermission, id=permission_id)
    elif permission_type == 'کاربر':
        permission = get_object_or_404(UserPermission, id=permission_id)
    else:
        return HttpResponseForbidden("نوع دسترسی نامعتبر است.")

    if request.method == 'POST':
        # ثبت فعالیت حذف دسترسی
        log_user_activity(
            user=request.user,
            activity_type='delete',
            description=f'حذف دسترسی {permission_id}',
            related_model='Permission',
            related_object_id=permission_id,
            url=reverse('permissions:list_permissions'),
            request=request
        )
        
        permission.delete()
        messages.success(request, "دسترسی با موفقیت حذف شد.")
        return redirect('permissions:list_permissions')

    # دریافت لیبل ویو
    views_with_labels = get_all_views_with_labels()
    view_label = permission.view_name
    for view in views_with_labels:
        if view['name'] == permission.view_name:
            view_label = view['label']
            break

    context = {
        'permission': permission,
        'permission_type': permission_type,
        'view_label': view_label,
    }
    return render(request, 'permissions/delete_permission.html', context)