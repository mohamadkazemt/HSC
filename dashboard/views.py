from django.shortcuts import render
from django.contrib.auth.decorators import login_required

import accounts.forms

name = 'dashboard'


@login_required(login_url='accounts:login')
def dashboard(request):
    is_admin_user = request.user.groups.filter(name='مدیر').exists()
    is_followup_user = request.user.groups.filter(name='مسئول پیگیری').exists()
    is_safety_officer = request.user.groups.filter(name='افسر ایمنی').exists()
    print(f' مدیر: {is_admin_user}')
    print(f'پیگیری:{is_followup_user}')
    print(f'ایمنی:{is_safety_officer}')

    context = {
        'is_admin_user': is_admin_user,
        'is_followup_user': is_followup_user,
        'is_safety_officer': is_safety_officer,
        'title': 'داشبورد',
    }

    return render(request, 'dashboard/dashboard.html',context)