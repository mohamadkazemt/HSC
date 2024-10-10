from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from dashboard.views import dashboard
from .forms import LoginForm
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

    return render(request, 'accounts/login.html', {'form': LoginForm()})



def user_logout(request):
    logout(request)
    return redirect('accounts:login')


def user_profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'accounts/overview.html')


from django.shortcuts import render, redirect
from .forms import UserForm, UserProfileForm
from django.contrib.auth.decorators import login_required

@login_required
def edit_profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)

        # بررسی فایل‌های آپلود شده
        print(request.FILES)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            print(f"فایل آپلود شده: {user_profile.image.url}")  # نمایش مسیر فایل ذخیره شده
            return redirect('accounts:profile')
        else:
            messages.error(request, 'لطفاً خطاهای زیر را برطرف کنید.')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)

    return render(request, 'accounts/settings.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })

