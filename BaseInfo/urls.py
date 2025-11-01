from django.urls import path
from . import views

app_name = 'baseinfo'

urlpatterns = [
    # تنظیمات پایه
    path('settings/', views.base_settings, name='base_settings'),
    
    # API endpoints for AJAX operations
    path('api/machines/', views.machines_api, name='machines_api'),
    path('api/machines/<int:pk>/', views.machine_detail_api, name='machine_detail_api'),
    path('api/blocks/', views.blocks_api, name='blocks_api'),
    path('api/blocks/<int:pk>/', views.block_detail_api, name='block_detail_api'),
    path('api/dumps/', views.dumps_api, name='dumps_api'),
    path('api/dumps/<int:pk>/', views.dump_detail_api, name='dump_detail_api'),
    path('api/emergency-vehicles/', views.emergency_vehicles_api, name='emergency_vehicles_api'),
    path('api/emergency-vehicles/<int:pk>/', views.emergency_vehicle_detail_api, name='emergency_vehicle_detail_api'),
    path('api/mineral-types/', views.mineral_types_api, name='mineral_types_api'),
    path('api/mineral-types/<int:pk>/', views.mineral_type_detail_api, name='mineral_type_detail_api'),
    path('api/workgroups/', views.workgroups_api, name='workgroups_api'),
    path('api/workgroups/<int:pk>/', views.workgroup_detail_api, name='workgroup_detail_api'),
    path('api/machine-types/', views.machine_types_api, name='machine_types_api'),
    path('api/machine-types/<int:pk>/', views.machine_type_detail_api, name='machine_type_detail_api'),
    
    # API for cascading dropdowns
    path('api/machine-types-by-workgroup/<int:workgroup_id>/', views.machine_types_by_workgroup, name='machine_types_by_workgroup'),
    
    # Import endpoints
    path('api/import/machines/', views.import_machines, name='import_machines'),
    path('api/import/blocks/', views.import_blocks, name='import_blocks'),
    path('api/import/dumps/', views.import_dumps, name='import_dumps'),
    path('api/import/vehicles/', views.import_vehicles, name='import_vehicles'),
    path('api/import/mineral-types/', views.import_mineral_types, name='import_mineral_types'),
    path('api/import/workgroups/', views.import_workgroups, name='import_workgroups'),
    path('api/import/machine-types/', views.import_machine_types, name='import_machine_types'),
]
