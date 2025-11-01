from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.admin.views.decorators import staff_member_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.db.models import Q
import json
import pandas as pd
import io

from .models import (
    MiningMachine, MiningBlock, Dump, EmergencyVehicle,
    MineralType, MachineryWorkGroup, TypeMachine
)
from contractor_management.models import Contractor


# Check if user is superuser
def is_superuser(user):
    return user.is_superuser


# =====================================================
# Base Settings Views
# =====================================================

@user_passes_test(is_superuser)
def base_settings(request):
    """صفحه اصلی تنظیمات پایه با تب‌ها"""
    context = {
        'machines': MiningMachine.objects.select_related('machine_workgroup', 'machine_type', 'contractor').all(),
        'blocks': MiningBlock.objects.all(),
        'dumps': Dump.objects.select_related('mineral_type').all(),
        'emergency_vehicles': EmergencyVehicle.objects.all(),
        'mineral_types': MineralType.objects.all(),
        'workgroups': MachineryWorkGroup.objects.all(),
        'machine_types': TypeMachine.objects.select_related('machine_workgroup').all(),
        'contractors': Contractor.objects.all(),
    }
    return render(request, 'BaseInfo/base_settings.html', context)


# =====================================================
# Mining Machines API
# =====================================================

@user_passes_test(is_superuser)
@require_http_methods(["GET", "POST"])
def machines_api(request):
    """مدیریت API دستگاه‌های معدنی"""
    if request.method == "GET":
        search = request.GET.get('search', '')
        machines = MiningMachine.objects.select_related(
            'machine_workgroup', 'machine_type', 'contractor'
        ).all()
        
        if search:
            machines = machines.filter(
                Q(workshop_code__icontains=search) |
                Q(machine_type__name__icontains=search)
            )
        
        data = [{
            'id': m.id,
            'workshop_code': m.workshop_code,
            'machine_type': m.machine_type.name if m.machine_type else '',
            'machine_workgroup': m.machine_workgroup.name if m.machine_workgroup else '',
            'ownership': m.get_ownership_display(),
            'contractor': m.contractor.name if m.contractor else '',
            'is_active': m.is_active,
        } for m in machines]
        
        return JsonResponse({'data': data})
    
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            machine = MiningMachine.objects.create(
                workshop_code=data.get('workshop_code'),
                machine_workgroup_id=data.get('machine_workgroup'),
                machine_type_id=data.get('machine_type'),
                ownership=data.get('ownership'),
                contractor_id=data.get('contractor') if data.get('contractor') else None,
                is_active=data.get('is_active', True)
            )
            return JsonResponse({
                'success': True,
                'message': 'دستگاه با موفقیت ایجاد شد',
                'data': {
                    'id': machine.id,
                    'workshop_code': machine.workshop_code,
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)


@user_passes_test(is_superuser)
@require_http_methods(["GET", "PUT", "DELETE"])
def machine_detail_api(request, pk):
    """جزئیات دستگاه معدنی"""
    machine = get_object_or_404(MiningMachine, pk=pk)
    
    if request.method == "GET":
        data = {
            'id': machine.id,
            'workshop_code': machine.workshop_code,
            'machine_workgroup': machine.machine_workgroup_id,
            'machine_type': machine.machine_type_id,
            'ownership': machine.ownership,
            'contractor': machine.contractor_id if machine.contractor else None,
            'is_active': machine.is_active,
        }
        return JsonResponse({'data': data})
    
    elif request.method == "PUT":
        try:
            data = json.loads(request.body)
            machine.workshop_code = data.get('workshop_code', machine.workshop_code)
            machine.machine_workgroup_id = data.get('machine_workgroup')
            machine.machine_type_id = data.get('machine_type')
            machine.ownership = data.get('ownership', machine.ownership)
            machine.contractor_id = data.get('contractor') if data.get('contractor') else None
            machine.is_active = data.get('is_active', machine.is_active)
            machine.save()
            return JsonResponse({
                'success': True,
                'message': 'دستگاه با موفقیت به‌روزرسانی شد'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    elif request.method == "DELETE":
        try:
            machine.delete()
            return JsonResponse({
                'success': True,
                'message': 'دستگاه با موفقیت حذف شد'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)


# =====================================================
# Mining Blocks API
# =====================================================

@user_passes_test(is_superuser)
@require_http_methods(["GET", "POST"])
def blocks_api(request):
    if request.method == "GET":
        blocks = MiningBlock.objects.all()
        data = [{
            'id': b.id,
            'block_name': b.block_name,
            'type': b.get_type_display(),
            'status': b.get_status_display(),
            'location': b.location,
            'is_active': b.is_active,
        } for b in blocks]
        return JsonResponse({'data': data})
    
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            block = MiningBlock.objects.create(
                block_name=data.get('block_name'),
                type=data.get('type'),
                status=data.get('status'),
                location=data.get('location', ''),
                is_active=data.get('is_active', True)
            )
            return JsonResponse({'success': True, 'message': 'بلوک با موفقیت ایجاد شد'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)


@user_passes_test(is_superuser)
@require_http_methods(["GET", "PUT", "DELETE"])
def block_detail_api(request, pk):
    block = get_object_or_404(MiningBlock, pk=pk)
    
    if request.method == "GET":
        data = {
            'id': block.id,
            'block_name': block.block_name,
            'type': block.type,
            'status': block.status,
            'location': block.location,
            'is_active': block.is_active,
        }
        return JsonResponse({'data': data})
    
    elif request.method == "PUT":
        try:
            data = json.loads(request.body)
            block.block_name = data.get('block_name', block.block_name)
            block.type = data.get('type', block.type)
            block.status = data.get('status', block.status)
            block.location = data.get('location', block.location)
            block.is_active = data.get('is_active', block.is_active)
            block.save()
            return JsonResponse({'success': True, 'message': 'بلوک با موفقیت به‌روزرسانی شد'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    elif request.method == "DELETE":
        try:
            block.delete()
            return JsonResponse({'success': True, 'message': 'بلوک با موفقیت حذف شد'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)


# =====================================================
# Dumps API  
# =====================================================

@user_passes_test(is_superuser)
@require_http_methods(["GET", "POST"])
def dumps_api(request):
    if request.method == "GET":
        dumps = Dump.objects.select_related('mineral_type').all()
        data = [{
            'id': d.id,
            'dump_name': d.dump_name,
            'location': d.location,
            'mineral_type': d.mineral_type.name if d.mineral_type else '',
            'is_active': d.is_active,
        } for d in dumps]
        return JsonResponse({'data': data})
    
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            dump = Dump.objects.create(
                dump_name=data.get('dump_name'),
                location=data.get('location', ''),
                mineral_type_id=data.get('mineral_type') if data.get('mineral_type') else None,
                is_active=data.get('is_active', True)
            )
            return JsonResponse({'success': True, 'message': 'دمپ با موفقیت ایجاد شد'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)


@user_passes_test(is_superuser)
@require_http_methods(["GET", "PUT", "DELETE"])
def dump_detail_api(request, pk):
    dump = get_object_or_404(Dump, pk=pk)
    
    if request.method == "GET":
        data = {
            'id': dump.id,
            'dump_name': dump.dump_name,
            'location': dump.location,
            'mineral_type': dump.mineral_type_id if dump.mineral_type else None,
            'is_active': dump.is_active,
        }
        return JsonResponse({'data': data})
    
    elif request.method == "PUT":
        try:
            data = json.loads(request.body)
            dump.dump_name = data.get('dump_name', dump.dump_name)
            dump.location = data.get('location', dump.location)
            dump.mineral_type_id = data.get('mineral_type') if data.get('mineral_type') else None
            dump.is_active = data.get('is_active', dump.is_active)
            dump.save()
            return JsonResponse({'success': True, 'message': 'دمپ با موفقیت به‌روزرسانی شد'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    elif request.method == "DELETE":
        try:
            dump.delete()
            return JsonResponse({'success': True, 'message': 'دمپ با موفقیت حذف شد'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)


# =====================================================
# Emergency Vehicles API
# =====================================================

@user_passes_test(is_superuser)
@require_http_methods(["GET", "POST"])
def emergency_vehicles_api(request):
    if request.method == "GET":
        vehicles = EmergencyVehicle.objects.all()
        data = [{
            'id': v.id,
            'vehicle_type': v.get_vehicle_type_display(),
            'workshop_code': v.workshop_code,
            'status': v.get_status_display(),
            'next_maintenance_date': v.next_maintenance_date.isoformat() if v.next_maintenance_date else '',
            'insurance_expiry': v.insurance_expiry.isoformat() if v.insurance_expiry else '',
        } for v in vehicles]
        return JsonResponse({'data': data})
    
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            vehicle = EmergencyVehicle.objects.create(
                vehicle_type=data.get('vehicle_type'),
                workshop_code=data.get('workshop_code'),
                license_plate=data.get('license_plate'),
                model=data.get('model'),
                manufacture_year=data.get('manufacture_year'),
                status=data.get('status'),
                last_maintenance_date=data.get('last_maintenance_date') if data.get('last_maintenance_date') else None,
                next_maintenance_date=data.get('next_maintenance_date') if data.get('next_maintenance_date') else None,
                insurance_expiry=data.get('insurance_expiry') if data.get('insurance_expiry') else None,
                technical_inspection_expiry=data.get('technical_inspection_expiry') if data.get('technical_inspection_expiry') else None,
                description=data.get('description', ''),
                has_horn=data.get('has_horn', True),
                has_hose=data.get('has_hose', True),
                has_monitor=data.get('has_monitor', True),
                has_extinguisher=data.get('has_extinguisher', True),
                has_equipment=data.get('has_equipment', True),
                has_foam=data.get('has_foam', True),
                has_water=data.get('has_water', True),
                has_tire=data.get('has_tire', True),
                has_brake=data.get('has_brake', True),
                has_lighting=data.get('has_lighting', True),
            )
            return JsonResponse({'success': True, 'message': 'خودروی امدادی با موفقیت ایجاد شد'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)


@user_passes_test(is_superuser)
@require_http_methods(["GET", "PUT", "DELETE"])
def emergency_vehicle_detail_api(request, pk):
    vehicle = get_object_or_404(EmergencyVehicle, pk=pk)
    
    if request.method == "GET":
        data = {
            'id': vehicle.id,
            'vehicle_type': vehicle.vehicle_type,
            'workshop_code': vehicle.workshop_code,
            'license_plate': vehicle.license_plate,
            'model': vehicle.model,
            'manufacture_year': vehicle.manufacture_year,
            'status': vehicle.status,
            'last_maintenance_date': vehicle.last_maintenance_date.isoformat() if vehicle.last_maintenance_date else '',
            'next_maintenance_date': vehicle.next_maintenance_date.isoformat() if vehicle.next_maintenance_date else '',
            'insurance_expiry': vehicle.insurance_expiry.isoformat() if vehicle.insurance_expiry else '',
            'technical_inspection_expiry': vehicle.technical_inspection_expiry.isoformat() if vehicle.technical_inspection_expiry else '',
            'description': vehicle.description,
            'has_horn': vehicle.has_horn,
            'has_hose': vehicle.has_hose,
            'has_monitor': vehicle.has_monitor,
            'has_extinguisher': vehicle.has_extinguisher,
            'has_equipment': vehicle.has_equipment,
            'has_foam': vehicle.has_foam,
            'has_water': vehicle.has_water,
            'has_tire': vehicle.has_tire,
            'has_brake': vehicle.has_brake,
            'has_lighting': vehicle.has_lighting,
        }
        return JsonResponse({'data': data})
    
    elif request.method == "PUT":
        try:
            data = json.loads(request.body)
            for field in ['vehicle_type', 'workshop_code', 'license_plate', 'model', 
                         'manufacture_year', 'status', 'description']:
                if field in data:
                    setattr(vehicle, field, data[field])
            
            for field in ['last_maintenance_date', 'next_maintenance_date', 
                         'insurance_expiry', 'technical_inspection_expiry']:
                if field in data:
                    setattr(vehicle, field, data[field] if data[field] else None)
            
            for field in ['has_horn', 'has_hose', 'has_monitor', 'has_extinguisher',
                         'has_equipment', 'has_foam', 'has_water', 'has_tire', 
                         'has_brake', 'has_lighting']:
                if field in data:
                    setattr(vehicle, field, data[field])
            
            vehicle.save()
            return JsonResponse({'success': True, 'message': 'خودروی امدادی با موفقیت به‌روزرسانی شد'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    elif request.method == "DELETE":
        try:
            vehicle.delete()
            return JsonResponse({'success': True, 'message': 'خودروی امدادی با موفقیت حذف شد'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)


# =====================================================
# Mineral Types API
# =====================================================

@user_passes_test(is_superuser)
@require_http_methods(["GET", "POST"])
def mineral_types_api(request):
    if request.method == "GET":
        types = MineralType.objects.all()
        data = [{'id': t.id, 'name': t.name, 'description': t.description} for t in types]
        return JsonResponse({'data': data})
    
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            mineral_type = MineralType.objects.create(
                name=data.get('name'),
                description=data.get('description', '')
            )
            return JsonResponse({'success': True, 'message': 'نوع سنگ معدنی با موفقیت ایجاد شد'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)


@user_passes_test(is_superuser)
@require_http_methods(["GET", "PUT", "DELETE"])
def mineral_type_detail_api(request, pk):
    mineral_type = get_object_or_404(MineralType, pk=pk)
    
    if request.method == "GET":
        data = {'id': mineral_type.id, 'name': mineral_type.name, 'description': mineral_type.description}
        return JsonResponse({'data': data})
    
    elif request.method == "PUT":
        try:
            data = json.loads(request.body)
            mineral_type.name = data.get('name', mineral_type.name)
            mineral_type.description = data.get('description', mineral_type.description)
            mineral_type.save()
            return JsonResponse({'success': True, 'message': 'نوع سنگ معدنی با موفقیت به‌روزرسانی شد'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    elif request.method == "DELETE":
        try:
            mineral_type.delete()
            return JsonResponse({'success': True, 'message': 'نوع سنگ معدنی با موفقیت حذف شد'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)


# =====================================================
# Workgroups API
# =====================================================

@user_passes_test(is_superuser)
@require_http_methods(["GET", "POST"])
def workgroups_api(request):
    if request.method == "GET":
        workgroups = MachineryWorkGroup.objects.all()
        data = [{'id': w.id, 'name': w.name, 'description': w.description} for w in workgroups]
        return JsonResponse({'data': data})
    
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            workgroup = MachineryWorkGroup.objects.create(
                name=data.get('name'),
                description=data.get('description', '')
            )
            return JsonResponse({'success': True, 'message': 'گروه کاری با موفقیت ایجاد شد'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)


@user_passes_test(is_superuser)
@require_http_methods(["GET", "PUT", "DELETE"])
def workgroup_detail_api(request, pk):
    workgroup = get_object_or_404(MachineryWorkGroup, pk=pk)
    
    if request.method == "GET":
        data = {'id': workgroup.id, 'name': workgroup.name, 'description': workgroup.description}
        return JsonResponse({'data': data})
    
    elif request.method == "PUT":
        try:
            data = json.loads(request.body)
            workgroup.name = data.get('name', workgroup.name)
            workgroup.description = data.get('description', workgroup.description)
            workgroup.save()
            return JsonResponse({'success': True, 'message': 'گروه کاری با موفقیت به‌روزرسانی شد'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    elif request.method == "DELETE":
        try:
            workgroup.delete()
            return JsonResponse({'success': True, 'message': 'گروه کاری با موفقیت حذف شد'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)


# =====================================================
# Machine Types API
# =====================================================

@user_passes_test(is_superuser)
@require_http_methods(["GET", "POST"])
def machine_types_api(request):
    if request.method == "GET":
        machine_types = TypeMachine.objects.select_related('machine_workgroup').all()
        data = [{
            'id': mt.id,
            'name': mt.name,
            'description': mt.description,
            'machine_workgroup': mt.machine_workgroup.name if mt.machine_workgroup else ''
        } for mt in machine_types]
        return JsonResponse({'data': data})
    
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            machine_type = TypeMachine.objects.create(
                name=data.get('name'),
                description=data.get('description', ''),
                machine_workgroup_id=data.get('machine_workgroup') if data.get('machine_workgroup') else None
            )
            return JsonResponse({'success': True, 'message': 'نوع دستگاه با موفقیت ایجاد شد'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)


@user_passes_test(is_superuser)
@require_http_methods(["GET", "PUT", "DELETE"])
def machine_type_detail_api(request, pk):
    machine_type = get_object_or_404(TypeMachine, pk=pk)
    
    if request.method == "GET":
        data = {
            'id': machine_type.id,
            'name': machine_type.name,
            'description': machine_type.description,
            'machine_workgroup': machine_type.machine_workgroup_id if machine_type.machine_workgroup else None
        }
        return JsonResponse({'data': data})
    
    elif request.method == "PUT":
        try:
            data = json.loads(request.body)
            machine_type.name = data.get('name', machine_type.name)
            machine_type.description = data.get('description', machine_type.description)
            machine_type.machine_workgroup_id = data.get('machine_workgroup') if data.get('machine_workgroup') else None
            machine_type.save()
            return JsonResponse({'success': True, 'message': 'نوع دستگاه با موفقیت به‌روزرسانی شد'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    elif request.method == "DELETE":
        try:
            machine_type.delete()
            return JsonResponse({'success': True, 'message': 'نوع دستگاه با موفقیت حذف شد'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)


# =====================================================
# Cascading Dropdown API
# =====================================================

@user_passes_test(is_superuser)
def machine_types_by_workgroup(request, workgroup_id):
    """فیلتر نوع دستگاه بر اساس گروه کاری"""
    machine_types = TypeMachine.objects.filter(machine_workgroup_id=workgroup_id)
    data = [{'id': mt.id, 'name': mt.name} for mt in machine_types]
    return JsonResponse({'data': data})


# =====================================================
# Import Endpoints
# =====================================================

@user_passes_test(is_superuser)
@require_http_methods(["POST"])
def import_machines(request):
    try:
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({'success': False, 'message': 'فایل انتخاب نشده'}, status=400)
        
        df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        created = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                MiningMachine.objects.create(
                    workshop_code=row.get('workshop_code', ''),
                    machine_workgroup_id=row.get('machine_workgroup_id'),
                    machine_type_id=row.get('machine_type_id'),
                    ownership=row.get('ownership', 'Company'),
                    contractor_id=row.get('contractor_id') if pd.notna(row.get('contractor_id')) else None,
                    is_active=bool(row.get('is_active', True))
                )
                created += 1
            except Exception as e:
                errors.append(f'ردیف {idx+1}: {str(e)}')
        
        return JsonResponse({
            'success': True,
            'message': f'{created} دستگاه ایجاد شد',
            'errors': errors
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@user_passes_test(is_superuser)
@require_http_methods(["POST"])
def import_blocks(request):
    try:
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({'success': False, 'message': 'فایل انتخاب نشده'}, status=400)
        
        df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        created = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                MiningBlock.objects.create(
                    block_name=row.get('block_name', ''),
                    type=row.get('type', 'w'),
                    status=row.get('status', 'initial_preparation'),
                    location=row.get('location', ''),
                    is_active=bool(row.get('is_active', True))
                )
                created += 1
            except Exception as e:
                errors.append(f'ردیف {idx+1}: {str(e)}')
        
        return JsonResponse({
            'success': True,
            'message': f'{created} بلوک ایجاد شد',
            'errors': errors
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@user_passes_test(is_superuser)
@require_http_methods(["POST"])
def import_dumps(request):
    try:
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({'success': False, 'message': 'فایل انتخاب نشده'}, status=400)
        
        df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        created = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                Dump.objects.create(
                    dump_name=row.get('dump_name', ''),
                    location=row.get('location', ''),
                    mineral_type_id=row.get('mineral_type_id') if pd.notna(row.get('mineral_type_id')) else None,
                    is_active=bool(row.get('is_active', True))
                )
                created += 1
            except Exception as e:
                errors.append(f'ردیف {idx+1}: {str(e)}')
        
        return JsonResponse({
            'success': True,
            'message': f'{created} دمپ ایجاد شد',
            'errors': errors
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@user_passes_test(is_superuser)
@require_http_methods(["POST"])
def import_vehicles(request):
    try:
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({'success': False, 'message': 'فایل انتخاب نشده'}, status=400)
        
        df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        created = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                EmergencyVehicle.objects.create(
                    vehicle_type=row.get('vehicle_type', 'fire_truck'),
                    workshop_code=row.get('workshop_code', ''),
                    license_plate=row.get('license_plate', ''),
                    model=row.get('model', ''),
                    manufacture_year=int(row.get('manufacture_year', 1400)),
                    status=row.get('status', 'active')
                )
                created += 1
            except Exception as e:
                errors.append(f'ردیف {idx+1}: {str(e)}')
        
        return JsonResponse({
            'success': True,
            'message': f'{created} خودرو ایجاد شد',
            'errors': errors
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@user_passes_test(is_superuser)
@require_http_methods(["POST"])
def import_mineral_types(request):
    try:
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({'success': False, 'message': 'فایل انتخاب نشده'}, status=400)
        
        df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        created = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                MineralType.objects.create(
                    name=row.get('name', ''),
                    description=row.get('description', '')
                )
                created += 1
            except Exception as e:
                errors.append(f'ردیف {idx+1}: {str(e)}')
        
        return JsonResponse({
            'success': True,
            'message': f'{created} نوع سنگ ایجاد شد',
            'errors': errors
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@user_passes_test(is_superuser)
@require_http_methods(["POST"])
def import_workgroups(request):
    try:
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({'success': False, 'message': 'فایل انتخاب نشده'}, status=400)
        
        df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        created = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                MachineryWorkGroup.objects.create(
                    name=row.get('name', ''),
                    description=row.get('description', '')
                )
                created += 1
            except Exception as e:
                errors.append(f'ردیف {idx+1}: {str(e)}')
        
        return JsonResponse({
            'success': True,
            'message': f'{created} گروه کاری ایجاد شد',
            'errors': errors
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@user_passes_test(is_superuser)
@require_http_methods(["POST"])
def import_machine_types(request):
    try:
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({'success': False, 'message': 'فایل انتخاب نشده'}, status=400)
        
        df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        created = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                TypeMachine.objects.create(
                    name=row.get('name', ''),
                    description=row.get('description', ''),
                    machine_workgroup_id=row.get('machine_workgroup_id') if pd.notna(row.get('machine_workgroup_id')) else None
                )
                created += 1
            except Exception as e:
                errors.append(f'ردیف {idx+1}: {str(e)}')
        
        return JsonResponse({
            'success': True,
            'message': f'{created} نوع دستگاه ایجاد شد',
            'errors': errors
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)
