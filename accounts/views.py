from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import PermissionDenied
from dashboard.views import dashboard
from .forms import LoginForm
from .forms import PasswordResetSMSForm
from accounts.models import UserProfile, DriverLicense, Section, Part, UnitGroup, Position, Payslip
from .organization_views import (
    organization_manage,
    organization_add,
    organization_edit,
    organization_delete,
    organization_merge
)
from .chart_views import organization_chart
from dashboard.sms_utils import send_template_sms
from .forms import UserForm, UserProfileForm,PasswordResetConfirmForm, ChangePasswordForm, DriverLicenseForm, PersonnelEditForm
from django.utils.timezone import now
from datetime import timedelta
import jdatetime
from django.db.models import Q, Count # اضافه کردن این خط
import logging
import pandas as pd
from io import BytesIO
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import PermissionDenied
from functools import wraps
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
import os
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib.auth.mixins import UserPassesTestMixin
from dashboard.utils import log_user_activity
from django.urls import reverse
from core.models import SiteSettings
from .notifications import notify_profile_updated, notify_organizational_updated, notify_password_reset


name = 'accounts'


def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped

logger = logging.getLogger(__name__)

def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')  # یا هر آدرس دیگری که برای داشبورد تعریف کرده‌اید

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)



        if user is not None:
            # جلوگیری از ورود پیمانکاران/پرسنل از مسیر عمومی
            if hasattr(user, 'contractor_profile') or hasattr(user, 'employee_profile'):
                return JsonResponse({'success': False, 'message': 'لطفاً از صفحه ورود پیمانکاران وارد شوید.'}, status=400)
            
            # جلوگیری از ورود پرسنل اورژانس از مسیر عمومی
            if user.groups.filter(name__in=['EmergencyManager', 'EmergencyDoctor', 'EmergencyNurse']).exists():
                return JsonResponse({'success': False, 'message': 'لطفاً از پورتال اورژانس وارد شوید.'}, status=400)
            
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
    user_profile = getattr(request.user, 'userprofile', None)
    
    # دریافت فیش‌های حقوقی کاربر (با try-except برای جلوگیری از خطا در صورت عدم وجود جدول)
    payslips = []
    if user_profile:
        try:
            payslips = list(user_profile.payslips.all().order_by('-year', '-month'))
            logger = logging.getLogger('django')
            logger.info(
                f"User Profile View - User: {request.user.username}, "
                f"Personnel Code: {user_profile.personnel_code}, "
                f"Payslips Count: {len(payslips)}"
            )
            if payslips:
                logger.info(f"Payslips found: {[f'{p.year}/{p.month:02d} (ID: {p.id})' for p in payslips]}")
            else:
                # بررسی اینکه آیا فیش‌هایی در دیتابیس وجود دارد
                all_payslips_count = Payslip.objects.count()
                user_payslips_count = Payslip.objects.filter(user_profile=user_profile).count()
                logger.info(
                    f"No payslips found for user. Total payslips in DB: {all_payslips_count}, "
                    f"User payslips count: {user_payslips_count}"
                )
        except Exception as e:
            # اگر جدول وجود نداشت، لیست خالی برمی‌گردانیم
            logger = logging.getLogger('django')
            logger.error(f"Error loading payslips for user {request.user.username}: {str(e)}", exc_info=True)
            payslips = []
    else:
        logger = logging.getLogger('django')
        logger.warning(f"User Profile View - No userprofile found for user: {request.user.username}")
    
    return render(request, 'accounts/overview.html', {
        'userprofile': user_profile,
        'payslips': payslips,  # اضافه کردن payslips به context
    })




@login_required
def edit_profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        password_form = ChangePasswordForm(request.user, request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = request.user
            user_form.save()
            profile = profile_form.save(commit=False)
            if 'image' in request.FILES:
                profile.image = request.FILES['image']
            profile.save()
            messages.success(request, 'پروفایل با موفقیت بروزرسانی شد.')

        if password_form.is_valid():
            if password_form.cleaned_data.get('old_password') and password_form.cleaned_data.get('new_password1') and password_form.cleaned_data.get('new_password2'):
                user = request.user
                user.set_password(password_form.cleaned_data['new_password1'])
                user.save()
                messages.success(request, 'رمز عبور با موفقیت تغییر یافت.')
                # لاگین مجدد کاربر بعد از تغییر رمز
                user = authenticate(username=user.username, password=password_form.cleaned_data['new_password1'])
                if user:
                    login(request, user)
        
        if not user_form.errors and not profile_form.errors and not password_form.errors:
            return redirect('accounts:profile')
        else:
            for field, errors in user_form.errors.items():
                for error in errors:
                    messages.error(request, f"خطا در فیلد {field}: {error}")
            for field, errors in profile_form.errors.items():
                for error in errors:
                    messages.error(request, f"خطا در فیلد {field}: {error}")
            for field, errors in password_form.errors.items():
                for error in errors:
                    messages.error(request, f"خطا در فیلد {field}: {error}")

    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)
        password_form = ChangePasswordForm(user=request.user)

    # Rubika connection code context
    try:
        from rubika_bot.models import RubikaConnectionCode
        code_obj = RubikaConnectionCode.objects.filter(user=request.user, used=False, expires_at__gt=now()).order_by('-created_at').first()
        if not code_obj:
            code_obj = RubikaConnectionCode.generate_for_user(request.user)
        rb_code = code_obj.code
        rb_expires = code_obj.expires_at
    except Exception:
        rb_code = ''
        rb_expires = None

    return render(request, 'accounts/settings.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'password_form': password_form,
        'userprofile': user_profile,
        'rubika_connection_code': rb_code,
        'rubika_expires_at': rb_expires,
    })



def send_reset_code(request):
    logger.info("send_reset_code called")
    if request.method == 'POST':
        logger.info("request method is POST")
        form = PasswordResetSMSForm(request.POST)
        if form.is_valid():
            logger.info("form is valid")
            username = form.cleaned_data['username']
            logger.info(f"username: {username}")
            try:
                user = User.objects.get(username=username)
                user_profile = UserProfile.objects.get(user=user)
                logger.info(f"user profile found: {user_profile}")
                user_profile.generate_verification_code()
                logger.info(f"verification code generated: {user_profile.verification_code}")

                # نمایش 3 رقم اول و 3 رقم آخر شماره موبایل
                mobile = user_profile.mobile
                masked_mobile = f"{mobile[:3]}******{mobile[-3:]}"
                request.session['masked_mobile'] = masked_mobile # شماره را در سشن ذخیره می کنیم

                 # ارسال پیامک
                template_id = 857178
                parameters = [
                    {"Name": "code", "Value": user_profile.verification_code},
                    {"Name": "username", "Value": user_profile.user.username}
                 ]
                send_template_sms(mobile, template_id, parameters)
                logger.info("sms sent successfully")
                return redirect('accounts:reset_password_confirm')

            except User.DoesNotExist:
                logger.error(f"user not found for username: {username}")
                form.add_error('username',"نام کاربری وارد شده یافت نشد.")
                return render(request, 'accounts/reset-password.html', {'form': form})
            except UserProfile.DoesNotExist:
                 logger.error(f"user profile not found for user: {user}")
                 form.add_error(None,"خطایی رخ داده است.")
                 return render(request, 'accounts/reset-password.html', {'form': form})
            except Exception as e:
                 logger.error(f"an error occurred {e}")
                 form.add_error(None,"خطایی رخ داده است.")
                 return render(request, 'accounts/reset-password.html', {'form': form})
        else:
            logger.error(f"form is not valid, errors:{form.errors}")
            return render(request, 'accounts/reset-password.html', {'form': form})
    else:
        form = PasswordResetSMSForm()
        logger.info("request method is GET")
    return render(request, 'accounts/reset-password.html', {'form': form})


def confirm_reset_code(request):
 masked_mobile = request.session.get('masked_mobile')
 if request.method == 'POST':
     form = PasswordResetConfirmForm(request.POST)
     if form.is_valid():
         code = form.cleaned_data['code']
         new_password = form.cleaned_data['new_password']
         try:
             user_profile = UserProfile.objects.get(verification_code=code)
             # بررسی اعتبار کد (مثلاً ۵ دقیقه)
             if user_profile.code_generated_at + timedelta(minutes=5) < now():
                 form.add_error('code', "کد تأیید منقضی شده است.")
                 return render(request, 'accounts/new-password.html', {'form': form,'masked_mobile':masked_mobile})


             # تغییر رمز عبور
             user = user_profile.user
             user.set_password(new_password)
             user.save()

             # پاک‌سازی کد تأیید
             user_profile.verification_code = None
             user_profile.code_generated_at = None
             user_profile.save()
             messages.success(request, "رمز عبور با موفقیت تغییر یافت.")
             del request.session['masked_mobile']
             return redirect('accounts:login')
         except UserProfile.DoesNotExist:
             form.add_error('code', "کد تأیید اشتباه است.")
             return render(request, 'accounts/new-password.html', {'form': form,'masked_mobile':masked_mobile})
     else:
         return render(request, 'accounts/new-password.html', {'form': form,'masked_mobile':masked_mobile})
 else:
     form = PasswordResetConfirmForm()
     return render(request, 'accounts/new-password.html', {'form': form,'masked_mobile':masked_mobile})

def get_users_ajax(request):
    users = []
    search_term = request.GET.get('term', '')
    if search_term:
        for user in User.objects.filter(Q(first_name__icontains=search_term) | 
                                      Q(last_name__icontains=search_term) | 
                                      Q(userprofile__personnel_code__icontains=search_term)):
            user_profile = getattr(user, 'userprofile', None)
            if user_profile:
                users.append({
                    "id": user_profile.id,
                    "name": f"{user.first_name} {user.last_name} ({user_profile.personnel_code})"
                })
    else:
        for user in User.objects.all():
            user_profile = getattr(user, 'userprofile', None)
            if user_profile:
                users.append({
                    "id": user_profile.id,
                    "name": f"{user.first_name} {user.last_name} ({user_profile.personnel_code})"
                })
    return JsonResponse(users, safe=False)

@login_required
def driver_license(request):
    try:
        driver_license = DriverLicense.objects.get(user=request.user)
        form = DriverLicenseForm(instance=driver_license)
    except DriverLicense.DoesNotExist:
        form = DriverLicenseForm()

    if request.method == 'POST':
        logger.info("[DriverLicense] POST received. raw expiry_date=%s", request.POST.get('expiry_date'))
        form = DriverLicenseForm(request.POST, request.FILES, instance=driver_license if 'driver_license' in locals() else None)
        logger.info("[DriverLicense] form.data expiry_date=%s", form.data.get('expiry_date'))
        if form.is_valid():
            cleaned_expiry = form.cleaned_data.get('expiry_date')
            logger.info("[DriverLicense] form.is_valid True. cleaned expiry_date=%s (type=%s)", cleaned_expiry, type(cleaned_expiry))
            license = form.save(commit=False)
            license.user = request.user
            logger.info("[DriverLicense] about to save: model.expiry_date(before set)=%s", getattr(license, 'expiry_date', None))
            license.save()
            logger.info("[DriverLicense] saved: model.expiry_date(after save)=%s (type=%s)", license.expiry_date, type(license.expiry_date))
            messages.success(request, 'اطلاعات گواهینامه با موفقیت ذخیره شد.')
            return redirect('accounts:profile')
        else:
            logger.error("[DriverLicense] form.is_valid False. errors=%s", form.errors.as_json())
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"خطا در فیلد {field}: {error}")

    return render(request, 'accounts/driver_license.html', {
        'form': form,
        'driver_license': driver_license if 'driver_license' in locals() else None
    })


@login_required
@superuser_required
def personnel_list(request):
    queryset = UserProfile.objects.select_related('user', 'section', 'part', 'unit_group', 'position').all()

    # Filters - validate and clean IDs
    def clean_id(value):
        """Clean and validate ID value - return None if invalid"""
        if not value or value == '' or value == 'None' or value == 'null':
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    section_id = clean_id(request.GET.get('section'))
    part_id = clean_id(request.GET.get('part'))
    unit_group_id = clean_id(request.GET.get('unit_group'))
    position_id = clean_id(request.GET.get('position'))
    q = request.GET.get('q', '').strip()

    # Check if query is purely numeric (likely a personnel code)
    # If searching by personnel code, prioritize it over hierarchical filters
    is_personnel_code_search = q and q.isdigit() and len(q) >= 3  # At least 3 digits to be considered a code
    
    # Apply hierarchical filters only if NOT searching by personnel code
    # (Personnel code search should work regardless of filters)
    if not is_personnel_code_search:
        if section_id:
            queryset = queryset.filter(
                Q(section_id=section_id) |
                Q(part__section_id=section_id) |
                Q(unit_group__part__section_id=section_id) |
                Q(position__unit_group__part__section_id=section_id)
            )
        if part_id:
            queryset = queryset.filter(
                Q(part_id=part_id) |
                Q(unit_group__part_id=part_id) |
                Q(position__unit_group__part_id=part_id)
            )
        if unit_group_id:
            queryset = queryset.filter(
                Q(unit_group_id=unit_group_id) |
                Q(position__unit_group_id=unit_group_id)
            )
        if position_id:
            queryset = queryset.filter(position_id=position_id)

    if q:
        # Clean search query - remove extra whitespace
        q_clean = q.strip()
        
        # Build comprehensive search conditions
        search_conditions = (
            Q(user__first_name__icontains=q_clean) |
            Q(user__last_name__icontains=q_clean)
        )
        
        # For personnel code: try multiple matching strategies
        # 1. Exact match (case insensitive) - highest priority
        # 2. Contains match (for partial codes or codes with whitespace)
        # 3. Startswith match (for codes that start with the query)
        # Also handle leading zeros and whitespace
        personnel_code_conditions = (
            Q(personnel_code__iexact=q_clean) |
            Q(personnel_code__icontains=q_clean) |
            Q(personnel_code__startswith=q_clean)
        )
        
        # Also try with leading zeros removed (in case code is stored as "0111264" but searched as "111264")
        if q_clean.isdigit():
            # Try exact match without leading zeros
            q_numeric = str(int(q_clean))  # Remove leading zeros
            if q_numeric != q_clean:
                personnel_code_conditions |= (
                    Q(personnel_code__iexact=q_numeric) |
                    Q(personnel_code__icontains=q_numeric) |
                    Q(personnel_code__startswith=q_numeric)
                )
        
        search_conditions |= personnel_code_conditions
        queryset = queryset.filter(search_conditions)

    # Stats based on filtered queryset
    total_count = queryset.count()
    
    # Helper function to normalize name (remove extra spaces, trim)
    def normalize_name(name):
        if not name:
            return 'نامشخص'
        # Remove extra whitespace and normalize (strip and collapse multiple spaces)
        normalized = ' '.join(str(name).strip().split())
        return normalized if normalized else 'نامشخص'
    
    # Helper function to merge duplicate items by normalized name
    def merge_duplicates(items, name_key, id_key):
        """Merge items with the same normalized name, summing their counts"""
        merged = {}
        for r in items:
            original_name = r.get(name_key) or 'نامشخص'
            normalized_name = normalize_name(original_name)
            item_id = r.get(id_key)
            count = r.get('count', 0)
            
            # Skip items with None ID (they should be displayed but not clickable)
            # Use normalized name as key
            if normalized_name not in merged:
                # Use the first ID we encounter (or the one with highest count)
                merged[normalized_name] = {
                    'name': normalized_name,  # Use normalized name for display
                    'count': count,
                    'id': item_id if item_id is not None else None,  # Keep None as None
                }
            else:
                # Merge: sum counts, keep ID with higher count (prefer non-None IDs)
                merged[normalized_name]['count'] += count
                # If current has ID and merged doesn't, or current has higher count, update
                if item_id is not None:
                    if merged[normalized_name]['id'] is None or count > merged[normalized_name]['count'] - count:
                        merged[normalized_name]['id'] = item_id
        
        # Convert to list and sort by count (None IDs last)
        result = list(merged.values())
        result.sort(key=lambda x: (x['id'] is None, -x['count'], x['name']))
        return result
    
    sections_stats = list(
        queryset.values('section_id', 'section__name').annotate(count=Count('id')).order_by('-count', 'section__name')
    )
    parts_stats = list(
        queryset.values('part_id', 'part__name').annotate(count=Count('id')).order_by('-count', 'part__name')
    )
    unit_groups_stats = list(
        queryset.values('unit_group_id', 'unit_group__name').annotate(count=Count('id')).order_by('-count', 'unit_group__name')
    )
    positions_stats = list(
        queryset.values('position_id', 'position__name').annotate(count=Count('id')).order_by('-count', 'position__name')
    )
    
    # Merge duplicates for each stat type
    stats = {
        'total': total_count,
        'sections': merge_duplicates(sections_stats, 'section__name', 'section_id'),
        'parts': merge_duplicates(parts_stats, 'part__name', 'part_id'),
        'unit_groups': merge_duplicates(unit_groups_stats, 'unit_group__name', 'unit_group_id'),
        'positions': merge_duplicates(positions_stats, 'position__name', 'position_id'),
    }

    # Pagination
    try:
        per_page = int(request.GET.get('per_page', 25))
    except (TypeError, ValueError):
        per_page = 25
    if per_page not in [10, 25, 50, 100, 200]:
        per_page = 25
    paginator = Paginator(queryset.order_by('user__last_name', 'user__first_name'), per_page)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    params = request.GET.copy()
    if 'page' in params:
        del params['page']
    query_string = params.urlencode()

    # Precomputed query strings for clickable stats (clear lower levels)
    def qs_without(keys):
        p = params.copy()
        for k in keys:
            if k in p:
                del p[k]
        return p.urlencode()
    qs_no_section = qs_without(['section', 'part', 'unit_group', 'position'])
    qs_no_part = qs_without(['part', 'unit_group', 'position'])
    qs_no_unit_group = qs_without(['unit_group', 'position'])
    qs_no_position = qs_without(['position'])

    context = {
        'page_obj': page_obj,
        'personnel': page_obj,  # backward compatibility
        'paginator': paginator,
        'is_paginated': paginator.num_pages > 1,
        'sections': Section.objects.all(),
        'parts': Part.objects.all(),
        'unit_groups': UnitGroup.objects.all(),
        'positions': Position.objects.all(),
        'stats': stats,
        'current_filters': {
            'section': section_id or '',
            'part': part_id or '',
            'unit_group': unit_group_id or '',
            'position': position_id or '',
            'q': q or '',
            'per_page': str(per_page),
        },
        'per_page_options': [10, 25, 50, 100, 200],
        'query_string': query_string,
        'qs_no_section': qs_no_section,
        'qs_no_part': qs_no_part,
        'qs_no_unit_group': qs_no_unit_group,
        'qs_no_position': qs_no_position,
    }
    return render(request, 'accounts/personnel_list.html', context)


@login_required
@superuser_required
def personnel_edit(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        form_type = request.POST.get('form_type', '')
        
        # Handle password reset
        if form_type == 'password_reset':
            new_password = request.POST.get('new_password', '').strip()
            confirm_password = request.POST.get('confirm_password', '').strip()
            
            if not new_password:
                messages.error(request, 'رمز عبور جدید نمی‌تواند خالی باشد.')
            elif len(new_password) < 8:
                messages.error(request, 'رمز عبور باید حداقل 8 کاراکتر باشد.')
            elif new_password != confirm_password:
                messages.error(request, 'رمز عبور و تأیید رمز عبور مطابقت ندارند.')
            else:
                user.set_password(new_password)
                user.save()
                notify_password_reset(user, actor=request.user)
                messages.success(request, f'رمز عبور کاربر {user.get_full_name() or user.username} با موفقیت تغییر یافت.')
                return redirect('accounts:personnel_edit', user_id=user_id)
        
        # Handle profile update (personal information)
        elif form_type == 'profile':
            # فقط فیلدهای اطلاعات شخصی را update می‌کنیم
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            personnel_code = request.POST.get('personnel_code', '').strip()
            mobile = request.POST.get('mobile', '').strip()
            
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            
            profile.personnel_code = personnel_code
            profile.mobile = mobile
            profile.save()
            
            notify_profile_updated(user, actor=request.user)
            messages.success(request, 'اطلاعات شخصی با موفقیت ذخیره شد.')
            return redirect('accounts:personnel_edit', user_id=user_id)
        
        # Handle organizational update
        elif form_type == 'organizational':
            # فقط فیلدهای اطلاعات سازمانی را update می‌کنیم
            section_id = request.POST.get('section')
            part_id = request.POST.get('part')
            unit_group_id = request.POST.get('unit_group')
            position_id = request.POST.get('position')
            group_id = request.POST.get('group')
            
            # Update با مقادیر None اگر خالی باشند
            profile.section_id = section_id if section_id else None
            profile.part_id = part_id if part_id else None
            profile.unit_group_id = unit_group_id if unit_group_id else None
            profile.position_id = position_id if position_id else None
            profile.group_id = group_id if group_id else None
            profile.save()
            
            notify_organizational_updated(user, actor=request.user)
            messages.success(request, 'اطلاعات سازمانی با موفقیت ذخیره شد.')
            return redirect('accounts:personnel_edit', user_id=user_id)
    
    # Load form for GET request
    form = PersonnelEditForm(instance=profile, user_instance=user)

    return render(request, 'accounts/personnel_edit.html', {
        'form': form,
        'edit_user': user,
        'profile': profile,
    })


@login_required
@superuser_required
def personnel_import(request):
    # Download sample template
    if request.method == 'GET' and request.GET.get('download') == 'sample':
        sample_data = {
            "کد پرسنلی": ["12345", "67890"],
            "نام": ["علی", "زهرا"],
            "نام خانوادگی": ["رضایی", "کاظمی"],
            "بخش": ["بخش 1", "بخش 2"],
            "قسمت": ["قسمت 1", "قسمت 2"],
            "گروه": ["گروه 1", "گروه 2"],
            "سمت": ["مدیر", "کارمند"],
            "موبایل": ["09123456789", "09387654321"],
            "کد ملی": ["1111111111", "2222222222"],
            "گروه کاری": ["A", "B"],
        }
        df = pd.DataFrame(sample_data)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='نمونه')
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=نمونه_کاربران.xlsx'
        return response

    if request.method == 'POST' and 'excel_file' in request.FILES:
        excel_file = request.FILES['excel_file']
        try:
            df = pd.read_excel(excel_file)
            errors = []

            required_columns = [
                'کد پرسنلی', 'نام', 'نام خانوادگی', 'بخش', 'قسمت',
                'گروه', 'سمت', 'موبایل', 'کد ملی',  'گروه کاری'
            ]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                messages.error(request, f"فایل بارگذاری شده دارای ستون‌های ناقص است: {', '.join(missing_columns)}")
                return redirect('accounts:personnel_import')

            for index, row in df.iterrows():
                try:
                    mobile = str(row['موبایل']).strip()
                    if mobile and not mobile.startswith('0'):
                        mobile = '0' + mobile

                    section_name = str(row['بخش']).strip()
                    part_name = str(row['قسمت']).strip()
                    unit_group_name = str(row['گروه']).strip()
                    position_name = str(row['سمت']).strip()
                    work_group = str(row['گروه کاری']).strip().upper()
                    personnel_code = str(row['کد پرسنلی']).strip()
                    national_id = str(row['کد ملی']).strip()
                    first_name = str(row['نام']).strip()
                    last_name = str(row['نام خانوادگی']).strip()

                    if not national_id:
                        errors.append(f"ردیف {index + 1}: کد ملی خالی است")
                        continue

                    # Normalize names: strip and normalize whitespace to prevent duplicates
                    def normalize_name(name):
                        if not name:
                            return ''
                        # Remove extra whitespace and normalize (strip and collapse multiple spaces)
                        return ' '.join(str(name).strip().split())
                    
                    # Helper function to find existing item by normalized name
                    def find_existing_by_normalized_name(queryset, name):
                        normalized = normalize_name(name)
                        for item in queryset:
                            if normalize_name(item.name) == normalized:
                                return item
                        return None
                    
                    section_name = normalize_name(row.get('بخش', ''))
                    part_name = normalize_name(row.get('قسمت', ''))
                    unit_group_name = normalize_name(row.get('گروه', ''))
                    position_name = normalize_name(row.get('سمت', ''))
                    
                    # Get or create hierarchy with normalized names (prevent duplicates)
                    section = None
                    if section_name:
                        existing = find_existing_by_normalized_name(Section.objects.all(), section_name)
                        if existing:
                            section = existing
                        else:
                            section, _ = Section.objects.get_or_create(name=section_name)
                    
                    part = None
                    if part_name:
                        if section:
                            existing = find_existing_by_normalized_name(Part.objects.filter(section=section), part_name)
                            if existing:
                                part = existing
                            else:
                                part, _ = Part.objects.get_or_create(name=part_name, section=section)
                        else:
                            existing = find_existing_by_normalized_name(Part.objects.all(), part_name)
                            if existing:
                                part = existing
                            else:
                                part, _ = Part.objects.get_or_create(name=part_name, section=section)
                    
                    unit_group = None
                    if unit_group_name:
                        if part:
                            existing = find_existing_by_normalized_name(UnitGroup.objects.filter(part=part), unit_group_name)
                            if existing:
                                unit_group = existing
                            else:
                                unit_group, _ = UnitGroup.objects.get_or_create(name=unit_group_name, part=part)
                    
                    position = None
                    if position_name:
                        if unit_group:
                            existing = find_existing_by_normalized_name(Position.objects.filter(unit_group=unit_group), position_name)
                            if existing:
                                position = existing
                            else:
                                position, _ = Position.objects.get_or_create(name=position_name, unit_group=unit_group)

                    # Check if personnel_code already exists - UPDATE only
                    if personnel_code:
                        user_profile = UserProfile.objects.filter(personnel_code=personnel_code).select_related('user').first()
                        if user_profile:
                            # Update existing user profile
                            updates = []
                            if first_name and user_profile.user.first_name != first_name:
                                user_profile.user.first_name = first_name
                                updates.append("نام")
                            if last_name and user_profile.user.last_name != last_name:
                                user_profile.user.last_name = last_name
                                updates.append("نام خانوادگی")
                            if mobile and user_profile.mobile != mobile:
                                user_profile.mobile = mobile
                                updates.append("شماره موبایل")
                            if section and user_profile.section != section:
                                user_profile.section = section
                                updates.append("بخش")
                            if part and user_profile.part != part:
                                user_profile.part = part
                                updates.append("قسمت")
                            if unit_group and user_profile.unit_group != unit_group:
                                user_profile.unit_group = unit_group
                                updates.append("گروه")
                            if position and user_profile.position != position:
                                user_profile.position = position
                                updates.append("سمت")
                            if work_group and user_profile.group != work_group:
                                user_profile.group = work_group
                                updates.append("گروه کاری")
                            
                            # Always save (even if no visible updates, to ensure data consistency)
                            user_profile.user.save()
                            user_profile.save()
                            
                            if updates:
                                messages.success(request, f"ردیف {index + 1} ({personnel_code}): {', '.join(updates)} به‌روزرسانی شد")
                            continue

                    # Create or update user by national_id
                    user, created = User.objects.update_or_create(
                        username=national_id,
                        defaults={
                            'first_name': first_name,
                            'last_name': last_name,
                            'email': f"{national_id}@example.com",
                        }
                    )

                    # Create profile if needed
                    UserProfile.objects.update_or_create(
                        user=user,
                        defaults={
                            'personnel_code': personnel_code,
                            'mobile': mobile,
                            'unit_group': unit_group,
                            'section': section,
                            'part': part,
                            'position': position,
                            'group': work_group,
                        }
                    )
                except Exception as e:
                    errors.append(f"ردیف {index + 1}: خطا در ذخیره‌سازی کاربر - {str(e)}")

            if errors:
                for err in errors:
                    messages.info(request, err)
            else:
                messages.success(request, 'کاربران با موفقیت وارد شدند.')
        except Exception as e:
            messages.error(request, f"خطا در پردازش فایل: {str(e)}")
        return redirect('accounts:personnel_import')

    return render(request, 'accounts/personnel_import.html')


@login_required
@superuser_required
def personnel_add(request):
    """Add new personnel manually"""
    from accounts.forms import PersonnelEditForm
    from django.contrib.auth.models import User
    import secrets
    import string
    
    if request.method == 'POST':
        # Get form data
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        personnel_code = request.POST.get('personnel_code', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        national_id = request.POST.get('national_id', '').strip()
        section_id = request.POST.get('section')
        part_id = request.POST.get('part')
        unit_group_id = request.POST.get('unit_group')
        position_id = request.POST.get('position')
        work_group = request.POST.get('group', '').strip().upper()
        
        # Validation
        if not first_name or not last_name:
            messages.error(request, 'نام و نام خانوادگی الزامی است.')
        elif not national_id:
            messages.error(request, 'کد ملی الزامی است.')
        elif User.objects.filter(username=national_id).exists():
            messages.error(request, f'کاربری با کد ملی {national_id} از قبل وجود دارد.')
        elif personnel_code and UserProfile.objects.filter(personnel_code=personnel_code).exists():
            messages.error(request, f'کاربری با کد پرسنلی {personnel_code} از قبل وجود دارد.')
        else:
            try:
                # Generate random password
                password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
                
                # Create user
                user = User.objects.create_user(
                    username=national_id,
                    first_name=first_name,
                    last_name=last_name,
                    email=f"{national_id}@example.com",
                    password=password
                )
                
                # Get or create hierarchy
                section = None
                part = None
                unit_group = None
                position = None
                
                if section_id:
                    section = Section.objects.get(pk=section_id)
                if part_id:
                    part = Part.objects.get(pk=part_id)
                if unit_group_id:
                    unit_group = UnitGroup.objects.get(pk=unit_group_id)
                if position_id:
                    position = Position.objects.get(pk=position_id)
                
                # Create profile
                profile = UserProfile.objects.create(
                    user=user,
                    personnel_code=personnel_code,
                    mobile=mobile,
                    section=section,
                    part=part,
                    unit_group=unit_group,
                    position=position,
                    group=work_group
                )
                
                messages.success(request, f'کاربر {first_name} {last_name} با موفقیت اضافه شد. رمز عبور پیش‌فرض: {password}')
                return redirect('accounts:personnel_edit', user_id=user.id)
            except Exception as e:
                messages.error(request, f'خطا در ایجاد کاربر: {str(e)}')
    
    # Get all options for dropdowns
    sections = Section.objects.all()
    parts = Part.objects.all()
    unit_groups = UnitGroup.objects.all()
    positions = Position.objects.all()
    
    return render(request, 'accounts/personnel_add.html', {
        'sections': sections,
        'parts': parts,
        'unit_groups': unit_groups,
        'positions': positions,
    })


@login_required
@superuser_required
def personnel_export(request):
    # Build filtered queryset (same logic as personnel_list)
    queryset = UserProfile.objects.select_related('user', 'section', 'part', 'unit_group', 'position').all()
    section_id = request.GET.get('section')
    part_id = request.GET.get('part')
    unit_group_id = request.GET.get('unit_group')
    position_id = request.GET.get('position')
    q = request.GET.get('q', '').strip()

    # Check if query is purely numeric (likely a personnel code)
    # If searching by personnel code, prioritize it over hierarchical filters
    is_personnel_code_search = q and q.isdigit() and len(q) >= 3  # At least 3 digits to be considered a code
    
    # Apply hierarchical filters only if NOT searching by personnel code
    # (Personnel code search should work regardless of filters)
    if not is_personnel_code_search:
        if section_id:
            queryset = queryset.filter(
                Q(section_id=section_id) |
                Q(part__section_id=section_id) |
                Q(unit_group__part__section_id=section_id) |
                Q(position__unit_group__part__section_id=section_id)
            )
        if part_id:
            queryset = queryset.filter(
                Q(part_id=part_id) |
                Q(unit_group__part_id=part_id) |
                Q(position__unit_group__part_id=part_id)
            )
        if unit_group_id:
            queryset = queryset.filter(
                Q(unit_group_id=unit_group_id) |
                Q(position__unit_group_id=unit_group_id)
            )
        if position_id:
            queryset = queryset.filter(position_id=position_id)

    if q:
        # Clean search query - remove extra whitespace
        q_clean = q.strip()
        
        # Build comprehensive search conditions
        search_conditions = (
            Q(user__first_name__icontains=q_clean) |
            Q(user__last_name__icontains=q_clean)
        )
        
        # For personnel code: try multiple matching strategies
        # 1. Exact match (case insensitive) - highest priority
        # 2. Contains match (for partial codes or codes with whitespace)
        # 3. Startswith match (for codes that start with the query)
        # Also handle leading zeros and whitespace
        personnel_code_conditions = (
            Q(personnel_code__iexact=q_clean) |
            Q(personnel_code__icontains=q_clean) |
            Q(personnel_code__startswith=q_clean)
        )
        
        # Also try with leading zeros removed (in case code is stored as "0111264" but searched as "111264")
        if q_clean.isdigit():
            # Try exact match without leading zeros
            q_numeric = str(int(q_clean))  # Remove leading zeros
            if q_numeric != q_clean:
                personnel_code_conditions |= (
                    Q(personnel_code__iexact=q_numeric) |
                    Q(personnel_code__icontains=q_numeric) |
                    Q(personnel_code__startswith=q_numeric)
                )
        
        search_conditions |= personnel_code_conditions
        queryset = queryset.filter(search_conditions)

    wb = Workbook()
    ws = wb.active
    ws.title = 'پرسنل'
    # RTL
    try:
        ws.sheet_view.rightToLeft = True
    except Exception:
        pass

    # Headers
    headers = [
        'نام کامل', 'کد ملی', 'کد پرسنلی', 'شماره موبایل', 'بخش', 'قسمت', 'گروه', 'سمت', 'گروه کاری'
    ]
    ws.append(headers)

    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='4F46E5', end_color='4F46E5', fill_type='solid')
    center = Alignment(horizontal='center', vertical='center')

    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center

    # Rows
    for up in queryset.order_by('user__last_name', 'user__first_name'):
        full_name = (up.user.get_full_name() or up.user.username).strip()
        national_id = up.user.username
        row = [
            full_name,
            national_id,
            up.personnel_code or '',
            up.mobile or '',
            getattr(up.section, 'name', '') or '',
            getattr(up.part, 'name', '') or '',
            getattr(up.unit_group, 'name', '') or '',
            getattr(up.position, 'name', '') or '',
            up.get_group_display() if getattr(up, 'group', '') else ''
        ]
        ws.append(row)

    # Basic formatting
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = f"A1:I{ws.max_row}"

    # Column widths
    widths = [25, 15, 12, 14, 18, 18, 18, 18, 12]
    for idx, w in enumerate(widths, start=1):
        ws.column_dimensions[chr(64 + idx)].width = w

    # Align data rows to right for Persian readability
    right = Alignment(horizontal='right', vertical='center')
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=9):
        for cell in row:
            cell.alignment = right

    # Stream to response
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    resp = HttpResponse(buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = 'attachment; filename=لیست_پرسنل.xlsx'
    return resp


@login_required
@superuser_required
def api_parts_by_section(request):
    section_id = request.GET.get('section')
    parts = Part.objects.filter(section_id=section_id).values('id', 'name') if section_id else []
    return JsonResponse(list(parts), safe=False)


@login_required
@superuser_required
def api_unit_groups_by_part(request):
    part_id = request.GET.get('part')
    unit_groups = UnitGroup.objects.filter(part_id=part_id).values('id', 'name') if part_id else []
    return JsonResponse(list(unit_groups), safe=False)


@login_required
@superuser_required
def api_positions_by_unit_group(request):
    ug_id = request.GET.get('unit_group')
    positions = Position.objects.filter(unit_group_id=ug_id).values('id', 'name') if ug_id else []
    return JsonResponse(list(positions), safe=False)


@login_required
@superuser_required
def batch_payslip_upload(request):
    """ویو برای آپلود دسته‌ای فیش‌های حقوقی"""
    if request.method == 'POST':
        year = request.POST.get('year')
        month = request.POST.get('month')
        files = request.FILES.getlist('files')
        
        if not year or not month:
            return JsonResponse({
                'success': False,
                'message': 'سال و ماه باید انتخاب شوند.'
            }, status=400)
        
        try:
            year = int(year)
            month = int(month)
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'سال و ماه باید عدد باشند.'
            }, status=400)
        
        if not files:
            return JsonResponse({
                'success': False,
                'message': 'حداقل یک فایل باید انتخاب شود.'
            }, status=400)
        
        success_count = 0
        errors = []
        success_files = []
        
        for file in files:
            try:
                # استخراج کد پرسنلی از نام فایل
                filename = file.name
                # حذف پسوند
                base_name = os.path.splitext(filename)[0]
                # استخراج کد پرسنلی (فرض می‌کنیم نام فایل همان کد پرسنلی است یا حاوی آن است)
                # می‌توانیم الگوهای مختلف را امتحان کنیم
                personnel_code = base_name.strip()
                
                # جستجوی پروفایل کاربر بر اساس کد پرسنلی
                try:
                    user_profile = UserProfile.objects.get(personnel_code=personnel_code)
                except UserProfile.DoesNotExist:
                    # اگر پیدا نشد، سعی می‌کنیم با الگوهای دیگر جستجو کنیم
                    # مثلاً اگر نام فایل به صورت "12345_1403_01.pdf" باشد
                    parts = base_name.split('_')
                    if len(parts) > 0:
                        personnel_code = parts[0].strip()
                        try:
                            user_profile = UserProfile.objects.get(personnel_code=personnel_code)
                        except UserProfile.DoesNotExist:
                            errors.append(f"فایل {filename}: کد پرسنلی '{personnel_code}' یافت نشد")
                            continue
                        except UserProfile.MultipleObjectsReturned:
                            # اگر چند پروفایل با این کد پرسنلی وجود دارد، اولین مورد را انتخاب می‌کنیم
                            user_profile = UserProfile.objects.filter(personnel_code=personnel_code).first()
                            errors.append(f"⚠️ فایل {filename}: چند پروفایل با کد '{personnel_code}' یافت شد. اولین مورد انتخاب شد.")
                    else:
                        errors.append(f"فایل {filename}: کد پرسنلی '{personnel_code}' یافت نشد")
                        continue
                except UserProfile.MultipleObjectsReturned:
                    # اگر چند پروفایل با این کد پرسنلی وجود دارد، اولین مورد را انتخاب می‌کنیم
                    user_profile = UserProfile.objects.filter(personnel_code=personnel_code).first()
                    errors.append(f"⚠️ فایل {filename}: چند پروفایل با کد '{personnel_code}' یافت شد. اولین مورد انتخاب شد.")
                
                # بررسی وجود فیش برای این ماه و سال
                try:
                    existing_payslip = Payslip.objects.filter(
                        user_profile=user_profile,
                        year=year,
                        month=month
                    ).first()
                except Exception:
                    # اگر جدول وجود نداشت، existing_payslip را None می‌کنیم
                    existing_payslip = None
                
                if existing_payslip:
                    # اگر فیش وجود دارد، فایل را جایگزین می‌کنیم
                    existing_payslip.file.delete()
                    existing_payslip.file = file
                    existing_payslip.uploaded_by = request.user
                    existing_payslip.save()
                    success_count += 1
                    success_files.append(f"{filename} → {user_profile.user.get_full_name()}")
                else:
                    # ایجاد فیش جدید
                    payslip = Payslip.objects.create(
                        user_profile=user_profile,
                        file=file,
                        month=month,
                        year=year,
                        uploaded_by=request.user
                    )
                    success_count += 1
                    success_files.append(f"{filename} → {user_profile.user.get_full_name()}")
                    
            except Exception as e:
                errors.append(f"فایل {filename}: خطا - {str(e)}")
        
        return JsonResponse({
            'success': True,
            'success_count': success_count,
            'total_count': len(files),
            'success_files': success_files,
            'errors': errors
        })
    
    # GET request - نمایش فرم
    # تبدیل سال میلادی به شمسی
    current_gregorian = now().date()
    current_jalali = jdatetime.date.fromgregorian(date=current_gregorian)
    current_year = current_jalali.year
    
    # ایجاد لیست سال‌های شمسی
    years = list(range(current_year - 5, current_year + 2))
    months = [
        (1, 'فروردین'), (2, 'اردیبهشت'), (3, 'خرداد'),
        (4, 'تیر'), (5, 'مرداد'), (6, 'شهریور'),
        (7, 'مهر'), (8, 'آبان'), (9, 'آذر'),
        (10, 'دی'), (11, 'بهمن'), (12, 'اسفند')
    ]
    
    return render(request, 'accounts/payslip_management.html', {
        'years': years,
        'months': months,
    })


@login_required
def payslip_archive(request):
    """نمایش آرشیو فیش‌های حقوقی کاربر"""
    user_profile = getattr(request.user, 'userprofile', None)
    if not user_profile:
        messages.error(request, 'پروفایل کاربری یافت نشد.')
        return redirect('accounts:profile')
    
    payslips = Payslip.objects.filter(user_profile=user_profile).order_by('-year', '-month')
    
    return render(request, 'accounts/payslip_archive.html', {
        'payslips': payslips,
    })


@login_required
def payslip_download(request, payslip_id):
    """دانلود فیش حقوقی با بررسی امنیتی کامل"""
    try:
        payslip = Payslip.objects.select_related('user_profile', 'user_profile__user').get(pk=payslip_id)
        
        # بررسی دسترسی: فقط کاربر مربوطه یا superuser می‌تواند دانلود کند
        if payslip.user_profile.user != request.user and not request.user.is_superuser:
            # لاگ کردن تلاش غیرمجاز
            logger = logging.getLogger('django.security')
            logger.warning(
                f"تلاش غیرمجاز برای دسترسی به فیش حقوقی: User={request.user.username}, "
                f"Payslip ID={payslip_id}, Owner={payslip.user_profile.user.username}"
            )
            raise PermissionDenied("شما اجازه دسترسی به این فیش را ندارید.")
        
        # بررسی وجود فایل
        if not payslip.file:
            messages.error(request, 'فایل فیش حقوقی یافت نشد.')
            return redirect('accounts:payslip_archive')
        
        # خواندن فایل و ارسال آن
        try:
            file_content = payslip.file.read()
            response = HttpResponse(file_content, content_type='application/pdf')
            # استفاده از نام فایل معنادار برای کاربر (نه نام فایل واقعی در سرور)
            filename = f"payslip_{payslip.user_profile.personnel_code}_{payslip.year}_{payslip.month:02d}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            # جلوگیری از cache کردن فایل‌های حساس
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
        except IOError as e:
            messages.error(request, f'خطا در خواندن فایل: {str(e)}')
            return redirect('accounts:payslip_archive')
            
    except Payslip.DoesNotExist:
        messages.error(request, 'فیش حقوقی یافت نشد.')
        return redirect('accounts:payslip_archive')
    except PermissionDenied:
        messages.error(request, 'شما اجازه دسترسی به این فیش را ندارید.')
        return redirect('accounts:payslip_archive')
