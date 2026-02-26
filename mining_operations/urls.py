from django.urls import path

from .views import (
    DumpCountSheetView,
    LoadingHaulingDetailView,
    LoadingHaulingListView,
    MachineActivityCreateView,
    export_loading_hauling_excel,
    export_machine_activity_excel,
    shift_personnel_options,
)

app_name = 'mining_operations'

URLS_WITH_LABELS = [
    {
        'path': 'machine-activity/create/',
        'view': MachineActivityCreateView.as_view(),
        'name': 'machine_activity_create',
        'label': 'عملیات معدنی_ثبت فعالیت ماشین',
    },
    {
        'path': 'loading-hauling/list/',
        'view': LoadingHaulingListView.as_view(),
        'name': 'loading_hauling_list',
        'label': 'عملیات معدنی_لیست گزارش حمل و بارگیری',
    },
    {
        'path': 'loading-hauling/report/',
        'view': LoadingHaulingDetailView.as_view(),
        'name': 'loading_hauling_detail',
        'label': 'عملیات معدنی_جزئیات گزارش حمل و بارگیری',
    },
    {
        'path': 'count-sheet/create/',
        'view': DumpCountSheetView.as_view(),
        'name': 'count_sheet_create',
        'label': 'عملیات معدنی_فرم شمارش دامپ کنترچی',
    },
    {
        'path': 'machine-activity/export-excel/',
        'view': export_machine_activity_excel,
        'name': 'machine_activity_export_excel',
        'label': 'عملیات معدنی_خروجی اکسل فعالیت ماشین',
    },
    {
        'path': 'loading-hauling/export-excel/',
        'view': export_loading_hauling_excel,
        'name': 'loading_hauling_export_excel',
        'label': 'عملیات معدنی_خروجی اکسل حمل و بارگیری',
    },
]

urlpatterns = [
    path(url['path'], url['view'], name=url['name']) for url in URLS_WITH_LABELS
]

urlpatterns += [
    path('api/shift-personnel/', shift_personnel_options, name='shift_personnel_options'),
]
