from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from .models import FireExtinguisherType, FireExtinguisher, ServiceRecord
from dashboard.models import Notification
from .forms import (
    FireExtinguisherTypeForm, FireExtinguisherForm, ServiceRecordForm,
    FireExtinguisherReplacementForm, FireExtinguisherLocationForm
)

@login_required
@csrf_exempt
def extinguisher_create_ajax(request):
    if request.method == 'POST':
        form = FireExtinguisherForm(request.POST)
        if form.is_valid():
            extinguisher = form.save()
            return JsonResponse({'success': True, 'id': extinguisher.pk}, status=201)
        else:
            # Return structured errors and 400 status so client can handle per-field errors
            errors = {k: [e['message'] for e in v] for k, v in form.errors.get_json_data().items()}
            return JsonResponse({'success': False, 'errors': errors, 'message': 'فرم معتبر نیست'}, status=400)
    else:
        return JsonResponse({'success': False, 'message': 'درخواست نامعتبر است'}, status=400)

@login_required
def dashboard(request):
    # Get counts for different statuses
    status_counts = {
        'operational': FireExtinguisher.objects.filter(status='OPERATIONAL').count(),
        'needs_maintenance': FireExtinguisher.objects.filter(status='NEEDS_MAINTENANCE').count(),
        'expired': FireExtinguisher.objects.filter(status='EXPIRED').count(),
        'reserved': FireExtinguisher.objects.filter(status='RESERVED').count(),
    }

    # Get upcoming service dates
    today = timezone.now().date()
    upcoming_services = FireExtinguisher.objects.filter(
        Q(next_scheduled_service_date__lte=today + timedelta(days=30)) |
        Q(pressure_test_due_date__lte=today + timedelta(days=30))
    ).select_related('extinguisher_type')

    # Get recent service records
    recent_services = ServiceRecord.objects.select_related(
        'extinguisher', 'performed_by_user'
    ).order_by('-service_date')[:10]

    context = {
        'status_counts': status_counts,
        'upcoming_services': upcoming_services,
        'recent_services': recent_services,
    }
    return render(request, 'fire_extinguisher_management/dashboard.html', context)

@login_required
def extinguisher_list(request):
    extinguishers = FireExtinguisher.objects.select_related('extinguisher_type')
    
    # Filtering
    status = request.GET.get('status')
    extinguisher_type = request.GET.get('type')
    search = request.GET.get('search')
    
    if status:
        extinguishers = extinguishers.filter(status=status)
    if extinguisher_type:
        extinguishers = extinguishers.filter(extinguisher_type_id=extinguisher_type)
    if search:
        extinguishers = extinguishers.filter(
            Q(serial_tag__icontains=search) |
            Q(manufacturer__icontains=search) |
            Q(model_number__icontains=search)
        )

    # Pagination
    paginator = Paginator(extinguishers, 20)
    page = request.GET.get('page')
    extinguishers = paginator.get_page(page)

    types = FireExtinguisherType.objects.all()

    # Additional choices and querysets used by the create modal
    from django.apps import apps
    LocationSection = apps.get_model('anomalis', 'LocationSection')
    MiningMachine = apps.get_model('BaseInfo', 'MiningMachine')

    sections = LocationSection.objects.all()
    machines = MiningMachine.objects.filter(is_active=True)
    existing_extinguishers = FireExtinguisher.objects.all()

    # Add form for the create modal
    create_form = FireExtinguisherForm()

    context = {
        'extinguishers': extinguishers,
        'types': types,
        'sections': sections,
        'machines': machines,
        'existing_extinguishers': existing_extinguishers,
        'current_status': status,
        'current_type': extinguisher_type,
        'current_search': search,
        'form': create_form,  # Add the form to context
    }
    return render(request, 'fire_extinguisher_management/extinguisher_list.html', context)

@login_required
def extinguisher_detail(request, pk):
    extinguisher = get_object_or_404(FireExtinguisher.objects.select_related('extinguisher_type'), pk=pk)
    service_records = extinguisher.servicerecord_set.select_related('performed_by_user').order_by('-service_date')
    # Prepare forms used by modals on the detail page
    service_record_form = ServiceRecordForm(initial={'extinguisher': extinguisher})
    location_form = FireExtinguisherLocationForm(initial={
        'location_type': extinguisher.location_type,
        'location_section': extinguisher.location_section,
        'location_machine': extinguisher.location_machine,
    })
    replacement_form = FireExtinguisherReplacementForm()
    # Additional querysets for selects
    from django.apps import apps
    LocationSection = apps.get_model('anomalis', 'LocationSection')
    MiningMachine = apps.get_model('BaseInfo', 'MiningMachine')
    sections = LocationSection.objects.all()
    machines = MiningMachine.objects.filter(is_active=True)
    reserved_extinguishers = FireExtinguisher.objects.filter(status='reserved', extinguisher_type=extinguisher.extinguisher_type)

    context = {
        'extinguisher': extinguisher,
        'service_records': service_records,
        'service_record_form': service_record_form,
        'location_form': location_form,
        'replacement_form': replacement_form,
        'sections': sections,
        'machines': machines,
        'reserved_extinguishers': reserved_extinguishers,
    }
    return render(request, 'fire_extinguisher_management/extinguisher_detail.html', context)

@login_required
def extinguisher_create(request):
    if request.method == 'POST':
        form = FireExtinguisherForm(request.POST)
        if form.is_valid():
            extinguisher = form.save()
            messages.success(request, 'کپسول با موفقیت ثبت شد.')
            return redirect('extinguisher_detail', pk=extinguisher.pk)
    else:
        form = FireExtinguisherForm()
    
    return render(request, 'fire_extinguisher_management/extinguisher_form.html', {'form': form})

@login_required
def extinguisher_edit(request, pk):
    extinguisher = get_object_or_404(FireExtinguisher, pk=pk)
    if request.method == 'POST':
        form = FireExtinguisherForm(request.POST, instance=extinguisher)
        if form.is_valid():
            form.save()
            messages.success(request, 'اطلاعات کپسول با موفقیت به‌روزرسانی شد.')
            return redirect('extinguisher_detail', pk=extinguisher.pk)
    else:
        form = FireExtinguisherForm(instance=extinguisher)
    
    return render(request, 'fire_extinguisher_management/extinguisher_form.html', {'form': form})

@login_required
def extinguisher_replace(request):
    if request.method == 'POST':
        form = FireExtinguisherReplacementForm(request.POST)
        if form.is_valid():
            old_extinguisher = form.cleaned_data['old_extinguisher']
            new_extinguisher = form.cleaned_data['new_extinguisher']
            notes = form.cleaned_data['replacement_notes']

            # Update old extinguisher
            old_extinguisher.status = 'DISPOSED'
            old_extinguisher.replaced_by_extinguisher = new_extinguisher
            old_extinguisher.save()

            # Update new extinguisher
            new_extinguisher.status = 'OPERATIONAL'
            new_extinguisher.replaces_extinguisher = old_extinguisher
            new_extinguisher.location_type = old_extinguisher.location_type
            new_extinguisher.location_section = old_extinguisher.location_section
            new_extinguisher.location_machine = old_extinguisher.location_machine
            new_extinguisher.save()

            # Create service record
            ServiceRecord.objects.create(
                extinguisher=new_extinguisher,
                service_date=timezone.now().date(),
                service_type='REPLACEMENT',
                performed_by_user=request.user,
                outcome='COMPLETED',
                actions_taken=f'جایگزینی کپسول {old_extinguisher.serial_tag} با {new_extinguisher.serial_tag}',
                notes=notes
            )

            messages.success(request, 'عملیات جایگزینی با موفقیت انجام شد.')
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'عملیات جایگزینی با موفقیت انجام شد.', 'new_pk': new_extinguisher.pk}, status=200)
            return redirect('fire_extinguisher_management:extinguisher_detail', pk=new_extinguisher.pk)
    else:
        form = FireExtinguisherReplacementForm()
    
    return render(request, 'fire_extinguisher_management/extinguisher_replace.html', {'form': form})

@login_required
def extinguisher_change_location(request, pk):
    extinguisher = get_object_or_404(FireExtinguisher, pk=pk)
    if request.method == 'POST':
        form = FireExtinguisherLocationForm(request.POST)
        if form.is_valid():
            extinguisher.location_type = form.cleaned_data['location_type']
            if form.cleaned_data['location_type'] == 'section':
                extinguisher.location_section = form.cleaned_data['location_section']
                extinguisher.location_machine = None
            else:
                extinguisher.location_machine = form.cleaned_data['location_machine']
                extinguisher.location_section = None
            extinguisher.save()

            # Create service record
            ServiceRecord.objects.create(
                extinguisher=extinguisher,
                service_date=timezone.now().date(),
                service_type='MAINTENANCE',
                performed_by_user=request.user,
                outcome='COMPLETED',
                actions_taken='تغییر مکان کپسول',
                notes=form.cleaned_data['notes']
            )

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'مکان کپسول با موفقیت تغییر کرد.'}, status=200)
            messages.success(request, 'مکان کپسول با موفقیت تغییر کرد.')
            return redirect('fire_extinguisher_management:extinguisher_detail', pk=extinguisher.pk)
    else:
        form = FireExtinguisherLocationForm(initial={
            'location_type': extinguisher.location_type,
            'location_section': extinguisher.location_section,
            'location_machine': extinguisher.location_machine
        })
    
    return render(request, 'fire_extinguisher_management/extinguisher_location.html', {
        'form': form,
        'extinguisher': extinguisher
    })

@login_required
def service_record_create(request, extinguisher_pk):
    extinguisher = get_object_or_404(FireExtinguisher, pk=extinguisher_pk)
    if request.method == 'POST':
        form = ServiceRecordForm(request.POST)
        if form.is_valid():
            service_record = form.save(commit=False)
            service_record.extinguisher = extinguisher
            service_record.performed_by_user = request.user
            service_record.save()

            # Update extinguisher status and dates
            extinguisher.last_serviced_date = service_record.service_date
            extinguisher.next_scheduled_service_date = extinguisher.calculate_next_service_date()
            extinguisher.pressure_test_due_date = extinguisher.calculate_pressure_test_date()

            if service_record.outcome == 'FAIL':
                extinguisher.status = 'NEEDS_MAINTENANCE'
            elif service_record.outcome == 'PASS':
                extinguisher.status = 'OPERATIONAL'

            extinguisher.save()

            # AJAX response on successful creation
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'سابقه سرویس با موفقیت ثبت شد.'}, status=201)
            messages.success(request, 'سابقه سرویس با موفقیت ثبت شد.')
            return redirect('fire_extinguisher_management:extinguisher_detail', pk=extinguisher.pk)
        else:
            # Return structured errors for AJAX clients
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                errors = {k: [e['message'] for e in v] for k, v in form.errors.get_json_data().items()}
                return JsonResponse({'success': False, 'errors': errors, 'message': 'فرم معتبر نیست'}, status=400)
            messages.error(request, 'فرم نامعتبر است.')
            return render(request, 'fire_extinguisher_management/service_record_form.html', {
                'form': form,
                'extinguisher': extinguisher
            })
    else:
        form = ServiceRecordForm(initial={'extinguisher': extinguisher})
    
    return render(request, 'fire_extinguisher_management/service_record_form.html', {
        'form': form,
        'extinguisher': extinguisher
    })

@login_required
def notification_list(request):
    notifications = request.user.notifications.order_by('-created_at')
    return render(request, 'fire_extinguisher_management/notification_list.html', {
        'notifications': notifications
    })

@login_required
def mark_notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})

@login_required
def extinguisher_details_api(request, pk):
    extinguisher = get_object_or_404(FireExtinguisher, pk=pk)
    
    # Get available extinguishers for replacement
    available_extinguishers = FireExtinguisher.objects.filter(
        status='RESERVED',
        extinguisher_type=extinguisher.extinguisher_type
    ).values('id', 'serial_tag', 'extinguisher_type__name')
    
    # Format the data for the API response
    available_extinguishers = [
        {
            'id': e['id'],
            'serial_tag': e['serial_tag'],
            'type': e['extinguisher_type__name']
        }
        for e in available_extinguishers
    ]
    
    # Include location information
    location = {
        'content_type': extinguisher.content_type_id,
        'object_id': extinguisher.object_id
    }
    
    return JsonResponse({
        'available_extinguishers': available_extinguishers,
        'location': location
    })
