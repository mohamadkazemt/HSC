from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from dashboard.views import dashboard
from .forms import User, UserEditForm
from .models import UserProfile

name = 'accounts'




def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)



        if user is not None:
            login(request, user)
            return JsonResponse({'success': True})  # لاگین موفق
        else:
            return JsonResponse({'success': False, 'message': 'Invalid login credentials'}, status=400)  # لاگین ناموفق

    return render(request, 'accounts/login.html', {'form': User()})



def user_logout(request):
    logout(request)
    return redirect('accounts:login')


def user_profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'accounts/overview.html')


@login_required
def edit_user(request):
    if request.method == 'POST':
        form = UserEditForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            user.email = form.cleaned_data['email']
            user.username = form.cleaned_data['username']
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.save()

            # Update user profile
            profile = user.userprofile
            profile.mobile = form.cleaned_data['mobile']
            if 'image' in request.FILES:
                profile.image = request.FILES['image']
            profile.save()

            return redirect('profile')  # فرض کنیم این URL به صفحه پروفایل بازگردانده می‌شود
    else:
        # مقادیر اولیه فرم را با اطلاعات فعلی کاربر پر کنید
        user = request.user
        initial_data = {
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'mobile': user.userprofile.mobile,
        }
        form = UserEditForm(initial=initial_data)

    return render(request, 'accounts/settings.html', {'form': form})