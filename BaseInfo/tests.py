from django.test import TestCase
from django.core.exceptions import ValidationError

from .models import (
    MineralType, MachineryWorkGroup, TypeMachine, MiningMachine, 
    MiningBlock, Dump, EmergencyVehicle
)
from contractor_management.models import Contractor


class MineralTypeModelTest(TestCase):
    def test_create_mineral_type(self):
        """تست ایجاد نوع سنگ معدنی"""
        mineral = MineralType.objects.create(
            name='آهن',
            description='سنگ آهن پرعیار'
        )
        
        self.assertEqual(str(mineral), 'آهن')
        self.assertEqual(mineral.description, 'سنگ آهن پرعیار')
        self.assertIsNotNone(mineral.id)


class MachineryWorkGroupModelTest(TestCase):
    def test_create_machinery_work_group(self):
        """تست ایجاد گروه کاری"""
        group = MachineryWorkGroup.objects.create(
            name='گروه بارگیری',
            description='گروه ماشین‌آلات بارگیری'
        )
        
        self.assertEqual(str(group), 'گروه بارگیری')
        self.assertIsNotNone(group.id)


class TypeMachineModelTest(TestCase):
    def setUp(self):
        self.work_group = MachineryWorkGroup.objects.create(
            name='گروه بارگیری'
        )
    
    def test_create_type_machine(self):
        """تست ایجاد نوع دستگاه"""
        machine_type = TypeMachine.objects.create(
            machine_workgroup=self.work_group,
            name='لودر',
            description='لودر چرخ لاستیکی'
        )
        
        self.assertEqual(str(machine_type), 'لودر')
        self.assertEqual(machine_type.machine_workgroup, self.work_group)


class MiningMachineModelTest(TestCase):
    def setUp(self):
        self.work_group = MachineryWorkGroup.objects.create(
            name='گروه بارگیری'
        )
        self.machine_type = TypeMachine.objects.create(
            machine_workgroup=self.work_group,
            name='لودر'
        )
        self.contractor = Contractor.objects.create(
            name='پیمانکار تست',
            contact_person='مدیر پروژه',
            phone='09123456789'
        )
    
    def test_create_company_machine(self):
        """تست ایجاد دستگاه شرکت"""
        machine = MiningMachine.objects.create(
            machine_workgroup=self.work_group,
            machine_type=self.machine_type,
            workshop_code='L001',
            ownership='Company'
        )
        
        self.assertEqual(str(machine), 'L001 - لودر')
        self.assertEqual(machine.ownership, 'Company')
        self.assertTrue(machine.is_active)
        self.assertIsNone(machine.contractor)
    
    def test_create_contractor_machine(self):
        """تست ایجاد دستگاه پیمانکار"""
        machine = MiningMachine.objects.create(
            machine_workgroup=self.work_group,
            machine_type=self.machine_type,
            workshop_code='CL001',
            ownership='Contractor',
            contractor=self.contractor
        )
        
        self.assertEqual(machine.ownership, 'Contractor')
        self.assertEqual(machine.contractor, self.contractor)


class MiningBlockModelTest(TestCase):
    def test_create_mining_block(self):
        """تست ایجاد بلوک معدنی"""
        block = MiningBlock.objects.create(
            block_name='بلوک A1',
            type='o',
            status='ready_for_drilling',
            location='شمال معدن'
        )
        
        self.assertEqual(str(block), 'بلوک A1')
        self.assertEqual(block.type, 'o')
        self.assertEqual(block.status, 'ready_for_drilling')
        self.assertTrue(block.is_active)
    
    def test_block_status_choices(self):
        """تست انتخاب‌های وضعیت بلوک"""
        valid_statuses = [
            'initial_preparation', 'ready_for_drilling', 
            'ready_for_blasting', 'ready_for_loading', 
            'loading', 'completed'
        ]
        
        for status in valid_statuses:
            block = MiningBlock.objects.create(
                block_name=f'بلوک {status}',
                type='w',
                status=status
            )
            self.assertEqual(block.status, status)


class DumpModelTest(TestCase):
    def setUp(self):
        self.mineral_type = MineralType.objects.create(name='آهن')
    
    def test_create_dump(self):
        """تست ایجاد دمپ"""
        dump = Dump.objects.create(
            dump_name='دمپ شماره 1',
            location='جنوب معدن',
            mineral_type=self.mineral_type
        )
        
        self.assertEqual(str(dump), 'دمپ شماره 1')
        self.assertEqual(dump.mineral_type, self.mineral_type)
        self.assertTrue(dump.is_active)


class EmergencyVehicleModelTest(TestCase):
    def test_create_fire_truck(self):
        """تست ایجاد خودروی آتش‌نشانی"""
        fire_truck = EmergencyVehicle.objects.create(
            vehicle_type='fire_truck',
            workshop_code='FT001',
            license_plate='12ا345یراء19',
            model='بنز آتش‌نشانی',
            manufacture_year=2020,
            status='active'
        )
        
        self.assertIn('خودروی آتش‌نشانی', str(fire_truck))
        self.assertEqual(fire_truck.workshop_code, 'FT001')
        self.assertEqual(fire_truck.vehicle_type, 'fire_truck')
        self.assertEqual(fire_truck.status, 'active')
    
    def test_create_ambulance(self):
        """تست ایجاد آمبولانس"""
        ambulance = EmergencyVehicle.objects.create(
            vehicle_type='ambulance',
            workshop_code='AMB001',
            license_plate='13ب456یران987',
            model='بنز آمبولانس',
            manufacture_year=2021
        )
        
        self.assertIn('آمبولانس', str(ambulance))
        self.assertEqual(ambulance.vehicle_type, 'ambulance')
        self.assertEqual(ambulance.status, 'active')  # default value
    
    def test_emergency_vehicle_equipment_flags(self):
        """تست پرچم‌های تجهیزات"""
        vehicle = EmergencyVehicle.objects.create(
            vehicle_type='fire_truck',
            workshop_code='TEST001',
            license_plate='TEST123',
            model='تست',
            manufacture_year=2020,
            has_horn=False,
            has_equipment=True
        )
        
        self.assertFalse(vehicle.has_horn)
        self.assertTrue(vehicle.has_equipment)
        # بقیه مقادیر پیش‌فرض True هستند
        self.assertTrue(vehicle.has_hose)
        self.assertTrue(vehicle.has_water)
