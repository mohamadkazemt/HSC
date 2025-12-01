# hse_docs/urls.py
from django.urls import path
from . import views

app_name = 'hse_docs'

urlpatterns = [
    # Public Views
    path('', views.public_folder_list, name='public_folder_list'),
    path('section/<int:id>/', views.view_section, name='view_section'),
    path('section/<int:section_id>/topic/<slug:topic_slug>/', views.view_section_topic, name='view_section_topic'),
    path('group/<int:id>/', views.view_group, name='view_group'),
    path('group/<int:group_id>/topic/<slug:topic_slug>/', views.view_group_topic, name='view_group_topic'),
    path('topic/<slug:slug>/', views.view_topic, name='view_topic'),
    path('document/<int:pk>/', views.document_detail, name='document_detail'),
    
    # Admin Views
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/upload/', views.upload_document, name='upload_document'),
    path('admin/edit/<int:pk>/', views.edit_document, name='edit_document'),
    path('admin/qr-center/', views.qr_center, name='qr_center'),
    path('admin/qr/<str:qr_type>/<str:obj_id>/', views.generate_qr_code, name='generate_qr'),
    path('admin/documents/', views.document_list, name='document_list'),
    path('admin/topics/', views.topic_list, name='topic_list'),
]

