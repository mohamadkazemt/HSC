# corrective_actions/urls.py
from django.urls import path
from . import views

app_name = 'corrective_actions'

urlpatterns = [
    path('', views.corrective_action_list, name='list'),
    path('create/', views.corrective_action_create, name='create'),
    path('<int:pk>/', views.corrective_action_detail, name='detail'),
    path('<int:pk>/update/', views.corrective_action_update, name='update'),
    path('action-step/<int:pk>/toggle-done/', views.action_step_toggle_done, name='action_step_toggle_done'),
    path('<int:pk>/update-status/', views.corrective_action_update_status, name='update_status'),
    # AI endpoints
    path('api/ai/generate-suggestions/', views.ai_generate_suggestions, name='ai_generate_suggestions'),
    path('api/ai/generate-root-cause/', views.ai_generate_root_cause, name='ai_generate_root_cause'),
]

