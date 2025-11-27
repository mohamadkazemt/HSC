from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Count, Q
from django.db import transaction
from django.urls import reverse
from .models import Section, Part, UnitGroup, Position, UserProfile
from functools import wraps
from django.core.exceptions import PermissionDenied


def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@login_required
@superuser_required
def organization_manage(request):
    """Main page for managing organization structure"""
    entity_type = request.GET.get('type', 'section')  # section, part, unit_group, position
    search_query = request.GET.get('q', '').strip()
    
    context = {
        'entity_type': entity_type,
        'search_query': search_query,
    }
    
    if entity_type == 'section':
        items = Section.objects.annotate(
            personnel_count=Count('userprofile', distinct=True),
            parts_count=Count('part', distinct=True)
        )
        # Apply search filter
        if search_query:
            items = items.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))
        items = items.order_by('name')
        context['items'] = items
        context['title'] = 'مدیریت بخش‌ها'
        
    elif entity_type == 'part':
        items = Part.objects.select_related('section').annotate(
            personnel_count=Count('userprofile', distinct=True),
            unit_groups_count=Count('unitgroup', distinct=True)
        )
        # Apply search filter
        if search_query:
            items = items.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query) |
                Q(section__name__icontains=search_query)
            )
        items = items.order_by('section__name', 'name')
        context['items'] = items
        context['sections'] = Section.objects.all()
        context['title'] = 'مدیریت قسمت‌ها'
        
    elif entity_type == 'unit_group':
        items = UnitGroup.objects.select_related('part__section').annotate(
            personnel_count=Count('userprofile', distinct=True),
            positions_count=Count('position', distinct=True)
        )
        # Apply search filter
        if search_query:
            items = items.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query) |
                Q(part__name__icontains=search_query) |
                Q(part__section__name__icontains=search_query)
            )
        items = items.order_by('part__section__name', 'part__name', 'name')
        context['items'] = items
        context['parts'] = Part.objects.select_related('section').all()
        context['title'] = 'مدیریت گروه‌ها'
        
    elif entity_type == 'position':
        items = Position.objects.select_related('unit_group__part__section').annotate(
            personnel_count=Count('userprofile', distinct=True)
        )
        # Apply search filter
        if search_query:
            items = items.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query) |
                Q(unit_group__name__icontains=search_query) |
                Q(unit_group__part__name__icontains=search_query) |
                Q(unit_group__part__section__name__icontains=search_query)
            )
        items = items.order_by('unit_group__part__section__name', 'unit_group__part__name', 'unit_group__name', 'name')
        context['items'] = items
        context['unit_groups'] = UnitGroup.objects.select_related('part__section').all()
        context['title'] = 'مدیریت سمت‌ها'
    
    return render(request, 'accounts/organization_manage.html', context)


@login_required
@superuser_required
def organization_add(request):
    """Add new organization entity"""
    entity_type = request.GET.get('type', 'section')
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            messages.error(request, 'نام الزامی است.')
            return redirect(f"{reverse('accounts:organization_manage')}?type={entity_type}")
        
        # Normalize name
        name = ' '.join(name.split())
        
        try:
            if entity_type == 'section':
                if Section.objects.filter(name=name).exists():
                    messages.error(request, 'بخشی با این نام از قبل وجود دارد.')
                else:
                    Section.objects.create(name=name, description=description)
                    messages.success(request, 'بخش با موفقیت اضافه شد.')
                    
            elif entity_type == 'part':
                section_id = request.POST.get('section')
                if not section_id:
                    messages.error(request, 'انتخاب بخش الزامی است.')
                else:
                    section = Section.objects.get(pk=section_id)
                    # Check for duplicates by normalized name
                    existing = Part.objects.filter(section=section)
                    for p in existing:
                        if ' '.join(p.name.split()) == name:
                            messages.error(request, 'قسمتی با این نام در این بخش از قبل وجود دارد.')
                            return redirect(f"{reverse('accounts:organization_manage')}?type={entity_type}")
                    Part.objects.create(name=name, section=section, description=description)
                    messages.success(request, 'قسمت با موفقیت اضافه شد.')
                    
            elif entity_type == 'unit_group':
                part_id = request.POST.get('part')
                if not part_id:
                    messages.error(request, 'انتخاب قسمت الزامی است.')
                else:
                    part = Part.objects.get(pk=part_id)
                    existing = UnitGroup.objects.filter(part=part)
                    for ug in existing:
                        if ' '.join(ug.name.split()) == name:
                            messages.error(request, 'گروهی با این نام در این قسمت از قبل وجود دارد.')
                            return redirect(f"{reverse('accounts:organization_manage')}?type={entity_type}")
                    UnitGroup.objects.create(name=name, part=part, description=description)
                    messages.success(request, 'گروه با موفقیت اضافه شد.')
                    
            elif entity_type == 'position':
                unit_group_id = request.POST.get('unit_group')
                if not unit_group_id:
                    messages.error(request, 'انتخاب گروه الزامی است.')
                else:
                    unit_group = UnitGroup.objects.get(pk=unit_group_id)
                    existing = Position.objects.filter(unit_group=unit_group)
                    for pos in existing:
                        if ' '.join(pos.name.split()) == name:
                            messages.error(request, 'سمتی با این نام در این گروه از قبل وجود دارد.')
                            return redirect(f"{reverse('accounts:organization_manage')}?type={entity_type}")
                    Position.objects.create(name=name, unit_group=unit_group, description=description)
                    messages.success(request, 'سمت با موفقیت اضافه شد.')
                    
        except Exception as e:
            messages.error(request, f'خطا در ایجاد: {str(e)}')
        
        return redirect(f"{reverse('accounts:organization_manage')}?type={entity_type}")
    
    return redirect('accounts:organization_manage')


@login_required
@superuser_required
def organization_edit(request, entity_type, entity_id):
    """Edit organization entity"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            messages.error(request, 'نام الزامی است.')
            return redirect(f"{reverse('accounts:organization_manage')}?type={entity_type}")
        
        name = ' '.join(name.split())
        
        try:
            if entity_type == 'section':
                entity = get_object_or_404(Section, pk=entity_id)
                if Section.objects.filter(name=name).exclude(pk=entity_id).exists():
                    messages.error(request, 'بخشی با این نام از قبل وجود دارد.')
                else:
                    entity.name = name
                    entity.description = description
                    entity.save()
                    messages.success(request, 'بخش با موفقیت ویرایش شد.')
                    
            elif entity_type == 'part':
                entity = get_object_or_404(Part, pk=entity_id)
                section_id = request.POST.get('section')
                if section_id:
                    entity.section = Section.objects.get(pk=section_id)
                if Part.objects.filter(name=name, section=entity.section).exclude(pk=entity_id).exists():
                    messages.error(request, 'قسمتی با این نام در این بخش از قبل وجود دارد.')
                else:
                    entity.name = name
                    entity.description = description
                    entity.save()
                    messages.success(request, 'قسمت با موفقیت ویرایش شد.')
                    
            elif entity_type == 'unit_group':
                entity = get_object_or_404(UnitGroup, pk=entity_id)
                part_id = request.POST.get('part')
                if part_id:
                    entity.part = Part.objects.get(pk=part_id)
                if UnitGroup.objects.filter(name=name, part=entity.part).exclude(pk=entity_id).exists():
                    messages.error(request, 'گروهی با این نام در این قسمت از قبل وجود دارد.')
                else:
                    entity.name = name
                    entity.description = description
                    entity.save()
                    messages.success(request, 'گروه با موفقیت ویرایش شد.')
                    
            elif entity_type == 'position':
                entity = get_object_or_404(Position, pk=entity_id)
                unit_group_id = request.POST.get('unit_group')
                if unit_group_id:
                    entity.unit_group = UnitGroup.objects.get(pk=unit_group_id)
                if Position.objects.filter(name=name, unit_group=entity.unit_group).exclude(pk=entity_id).exists():
                    messages.error(request, 'سمتی با این نام در این گروه از قبل وجود دارد.')
                else:
                    entity.name = name
                    entity.description = description
                    entity.save()
                    messages.success(request, 'سمت با موفقیت ویرایش شد.')
                    
        except Exception as e:
            messages.error(request, f'خطا در ویرایش: {str(e)}')
        
        return redirect(f"{reverse('accounts:organization_manage')}?type={entity_type}")
    
    return redirect('accounts:organization_manage')


@login_required
@superuser_required
def organization_delete(request, entity_type, entity_id):
    """Delete organization entity"""
    if request.method == 'POST':
        try:
            if entity_type == 'section':
                entity = get_object_or_404(Section, pk=entity_id)
                personnel_count = UserProfile.objects.filter(section=entity).count()
                if personnel_count > 0:
                    messages.error(request, f'این بخش دارای {personnel_count} پرسنل است و نمی‌تواند حذف شود.')
                else:
                    entity.delete()
                    messages.success(request, 'بخش با موفقیت حذف شد.')
                    
            elif entity_type == 'part':
                entity = get_object_or_404(Part, pk=entity_id)
                personnel_count = UserProfile.objects.filter(part=entity).count()
                if personnel_count > 0:
                    messages.error(request, f'این قسمت دارای {personnel_count} پرسنل است و نمی‌تواند حذف شود.')
                else:
                    entity.delete()
                    messages.success(request, 'قسمت با موفقیت حذف شد.')
                    
            elif entity_type == 'unit_group':
                entity = get_object_or_404(UnitGroup, pk=entity_id)
                personnel_count = UserProfile.objects.filter(unit_group=entity).count()
                if personnel_count > 0:
                    messages.error(request, f'این گروه دارای {personnel_count} پرسنل است و نمی‌تواند حذف شود.')
                else:
                    entity.delete()
                    messages.success(request, 'گروه با موفقیت حذف شد.')
                    
            elif entity_type == 'position':
                entity = get_object_or_404(Position, pk=entity_id)
                personnel_count = UserProfile.objects.filter(position=entity).count()
                if personnel_count > 0:
                    messages.error(request, f'این سمت دارای {personnel_count} پرسنل است و نمی‌تواند حذف شود.')
                else:
                    entity.delete()
                    messages.success(request, 'سمت با موفقیت حذف شد.')
                    
        except Exception as e:
            messages.error(request, f'خطا در حذف: {str(e)}')
        
        return redirect(f"{reverse('accounts:organization_manage')}?type={entity_type}")
    
    return redirect('accounts:organization_manage')


@login_required
@superuser_required
def organization_merge(request, entity_type):
    """Merge two organization entities"""
    if request.method == 'POST':
        source_id = request.POST.get('source_id')
        target_id = request.POST.get('target_id')
        
        if not source_id or not target_id or source_id == target_id:
            messages.error(request, 'لطفاً دو مورد مختلف را انتخاب کنید.')
            return redirect(f"{reverse('accounts:organization_manage')}?type={entity_type}")
        
        try:
            with transaction.atomic():
                if entity_type == 'section':
                    source = get_object_or_404(Section, pk=source_id)
                    target = get_object_or_404(Section, pk=target_id)
                    # Update all related parts
                    Part.objects.filter(section=source).update(section=target)
                    # Update all user profiles
                    UserProfile.objects.filter(section=source).update(section=target)
                    source.delete()
                    messages.success(request, f'بخش "{source.name}" با "{target.name}" ادغام شد.')
                    
                elif entity_type == 'part':
                    source = get_object_or_404(Part, pk=source_id)
                    target = get_object_or_404(Part, pk=target_id)
                    # Update all related unit groups
                    UnitGroup.objects.filter(part=source).update(part=target)
                    # Update all user profiles
                    UserProfile.objects.filter(part=source).update(part=target)
                    source.delete()
                    messages.success(request, f'قسمت "{source.name}" با "{target.name}" ادغام شد.')
                    
                elif entity_type == 'unit_group':
                    source = get_object_or_404(UnitGroup, pk=source_id)
                    target = get_object_or_404(UnitGroup, pk=target_id)
                    # Update all related positions
                    Position.objects.filter(unit_group=source).update(unit_group=target)
                    # Update all user profiles
                    UserProfile.objects.filter(unit_group=source).update(unit_group=target)
                    source.delete()
                    messages.success(request, f'گروه "{source.name}" با "{target.name}" ادغام شد.')
                    
                elif entity_type == 'position':
                    source = get_object_or_404(Position, pk=source_id)
                    target = get_object_or_404(Position, pk=target_id)
                    # Update all user profiles
                    UserProfile.objects.filter(position=source).update(position=target)
                    source.delete()
                    messages.success(request, f'سمت "{source.name}" با "{target.name}" ادغام شد.')
                    
        except Exception as e:
            messages.error(request, f'خطا در ادغام: {str(e)}')
        
        return redirect(f"{reverse('accounts:organization_manage')}?type={entity_type}")
    
    return redirect('accounts:organization_manage')

