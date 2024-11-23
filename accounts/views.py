from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from dashboard.views import dashboard
from .forms import LoginForm
from .forms import PasswordResetSMSForm
from accounts.models import UserProfile
from dashboard.sms_utils import send_template_sms
from .forms import UserForm, UserProfileForm,PasswordResetConfirmForm
from django.utils.timezone import now
from datetime import timedelta

name = 'accounts'




def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')  # یا هر آدرس دیگری که برای داشبورد تعریف کرده‌اید

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




def send_reset_code(request):
    if request.method == 'POST':
        form = PasswordResetSMSForm(request.POST)
        if form.is_valid():
            mobile = form.cleaned_data['mobile']
            try:
                user_profile = UserProfile.objects.get(mobile=mobile)
                user_profile.generate_verification_code()

                # ارسال پیامک
                template_id = 857178  # شناسه قالب پیامک
                parameters = [
                    {"Name": "code", "Value": user_profile.verification_code},
                    {"Name": "username", "Value": user_profile.user.username}
                ]
                send_template_sms(mobile, template_id, parameters)
                messages.success(request, "کد تأیید به شماره موبایل ارسال شد.")
                return redirect('accounts:reset_password_confirm')
            except UserProfile.DoesNotExist:
                messages.error(request, "شماره موبایل وارد شده یافت نشد.")
    else:
        form = PasswordResetSMSForm()

    return render(request, 'accounts/reset-password.html', {'form': form})





def confirm_reset_code(request):
    if request.method == 'POST':
        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            new_password = form.cleaned_data['new_password']
            try:
                user_profile = UserProfile.objects.get(verification_code=code)
                # بررسی اعتبار کد (مثلاً ۵ دقیقه)
                if user_profile.code_generated_at + timedelta(minutes=5) < now():
                    messages.error(request, "کد تأیید منقضی شده است.")
                    return redirect('accounts:send_reset_code')

                # تغییر رمز عبور
                user = user_profile.user
                user.set_password(new_password)
                user.save()

                # پاک‌سازی کد تأیید
                user_profile.verification_code = None
                user_profile.code_generated_at = None
                user_profile.save()

                messages.success(request, "رمز عبور با موفقیت تغییر یافت.")
                return redirect('accounts:login')
            except UserProfile.DoesNotExist:
                messages.error(request, "کد تأیید اشتباه است.")
    else:
        form = PasswordResetConfirmForm()

    return render(request, 'accounts/new-password.html', {'form': form})
