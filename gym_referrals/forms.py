from django import forms
from django.utils import timezone
import jdatetime

from django.contrib.auth import get_user_model
from .models import Gym, GymContract, GymOperator, Referral


_PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
SELECT_CLASSES = "gym-native-select w-full bg-white text-gray-900 dark:border-gray-600 dark:bg-gray-700 dark:text-white"


class JalaliDateField(forms.Field):
    default_error_messages = {"invalid": "تاریخ شمسی معتبر وارد کنید؛ مثال: ۱۴۰۵/۰۱/۱۵."}

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", forms.TextInput(attrs={
            "class": "jalali-date w-full bg-white text-gray-900 dark:border-gray-600 dark:bg-gray-700 dark:text-white",
            "placeholder": "۱۴۰۵/۰۱/۱۵", "autocomplete": "off", "inputmode": "numeric",
        }))
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if value in self.empty_values:
            return None
        if hasattr(value, "year") and not isinstance(value, str):
            return value
        try:
            normalized = str(value).translate(_PERSIAN_DIGITS).strip().replace("-", "/")
            year, month, day = map(int, normalized.split("/"))
            return jdatetime.date(year, month, day).togregorian()
        except (TypeError, ValueError, OverflowError):
            raise forms.ValidationError(self.error_messages["invalid"], code="invalid")

    def prepare_value(self, value):
        if not value:
            return ""
        if isinstance(value, str):
            return value
        return jdatetime.date.fromgregorian(date=value).strftime("%Y/%m/%d")


class RialDecimalField(forms.DecimalField):
    def to_python(self, value):
        if isinstance(value, str):
            value = value.translate(_PERSIAN_DIGITS).replace(",", "").replace("٬", "").strip()
        return super().to_python(value)


class ReferralCreateForm(forms.Form):
    beneficiary = forms.ChoiceField(choices=(), label="فرد موردنظر")
    gym = forms.ModelChoiceField(queryset=Gym.objects.none(), label="باشگاه")

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [("", "فرد موردنظر را انتخاب کنید")]
        profile = getattr(user, "userprofile", None) if user and user.is_authenticated else None
        if profile:
            full_name = user.get_full_name().strip() or user.username
            choices.append((f"{Referral.BeneficiaryType.EMPLOYEE}:{profile.pk}", f"{full_name} — خودم"))
            choices.extend(
                (f"{Referral.BeneficiaryType.DEPENDENT}:{item.pk}", f"{item.first_name} {item.last_name} — {item.relationship or 'تحت تکفل'}")
                for item in profile.dependents.all()
            )
        self.fields["beneficiary"].choices = choices
        self.fields["beneficiary"].widget.attrs.update({"class": SELECT_CLASSES, "dir": "rtl"})
        today = timezone.localdate()
        self.fields["gym"].queryset = Gym.objects.filter(
            is_active=True, contracts__is_active=True,
            contracts__start_date__lte=today, contracts__end_date__gte=today,
        ).distinct()
        self.fields["gym"].empty_label = "باشگاه موردنظر را انتخاب کنید"
        self.fields["gym"].widget.attrs.update({"class": SELECT_CLASSES, "aria-describedby": "gym-help", "dir": "rtl"})

    def clean_beneficiary(self):
        value = self.cleaned_data["beneficiary"]
        try:
            beneficiary_type, beneficiary_id = value.split(":", 1)
            beneficiary_id = int(beneficiary_id)
        except (TypeError, ValueError):
            raise forms.ValidationError("فرد انتخاب‌شده معتبر نیست.")
        if beneficiary_type not in Referral.BeneficiaryType.values:
            raise forms.ValidationError("نوع فرد انتخاب‌شده معتبر نیست.")
        self.cleaned_data["beneficiary_type"] = beneficiary_type
        self.cleaned_data["beneficiary_id"] = beneficiary_id
        return value


class ReferralCancelForm(forms.Form):
    reason = forms.CharField(max_length=500, label="علت لغو", widget=forms.Textarea(attrs={"rows": 3}))


class LegacyImportForm(forms.Form):
    max_file_bytes = 5 * 1024 * 1024
    file = forms.FileField(label="فایل CSV یا Excel", widget=forms.FileInput(attrs={"accept": ".csv,.xlsx,.xls"}))

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        if uploaded.size > self.max_file_bytes:
            raise forms.ValidationError("حجم فایل باید کمتر از ۵ مگابایت باشد.")
        name = uploaded.name.lower()
        if not name.endswith((".csv", ".xlsx", ".xls")):
            raise forms.ValidationError("فرمت فایل مجاز نیست. فقط CSV یا Excel (.xlsx) پذیرفته می‌شود.")
        return uploaded


class InvoiceGenerateForm(forms.Form):
    contract = forms.ModelChoiceField(queryset=GymContract.objects.select_related("gym").filter(is_active=True), label="قرارداد")
    year = forms.IntegerField(min_value=2000, max_value=2200, label="سال میلادی")
    month = forms.IntegerField(min_value=1, max_value=12, label="ماه")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["contract"].empty_label = "قرارداد موردنظر را انتخاب کنید"
        for field in self.fields.values():
            field.widget.attrs["class"] = SELECT_CLASSES if isinstance(field.widget, forms.Select) else "w-full bg-white text-gray-900 dark:border-gray-600 dark:bg-gray-700 dark:text-white"


class InvoiceAdjustmentForm(forms.Form):
    adjustment_amount = forms.DecimalField(max_digits=16, decimal_places=2, label="تعدیل")
    notes = forms.CharField(required=True, widget=forms.Textarea(attrs={"rows": 3}), label="علت تعدیل")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "w-full bg-white text-gray-900 dark:border-gray-600 dark:bg-gray-700 dark:text-white"


class GymForm(forms.ModelForm):
    account_username = forms.CharField(
        required=False, label="نام کاربری ورود باشگاه",
        help_text="خالی بگذارید تا به‌صورت خودکار از کد باشگاه ساخته شود.",
        widget=forms.TextInput(attrs={"class": "gym-native-select w-full bg-white text-gray-900 dark:border-gray-600 dark:bg-gray-700 dark:text-white", "placeholder": "به‌صورت خودکار"}),
    )
    account_password = forms.CharField(
        required=False, label="رمز عبور اولیه باشگاه",
        help_text="خالی بگذارید تا رمز امن تصادفی ساخته شود (برای ورود اولیه از همین رمز استفاده کنید).",
        widget=forms.PasswordInput(attrs={"class": "gym-native-select w-full bg-white text-gray-900 dark:border-gray-600 dark:bg-gray-700 dark:text-white", "autocomplete": "new-password"}),
    )

    class Meta:
        model = Gym
        fields = ("name", "code", "phone", "address", "is_active")
        labels = {"name": "نام باشگاه", "code": "کد باشگاه", "phone": "شماره تماس", "address": "آدرس", "is_active": "فعال"}
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields.pop("account_username")
            self.fields.pop("account_password")
        for name, field in self.fields.items():
            if name not in ("account_username", "account_password") and name != "is_active":
                field.widget.attrs["class"] = SELECT_CLASSES if isinstance(field.widget, forms.Select) else "w-full bg-white text-gray-900 dark:border-gray-600 dark:bg-gray-700 dark:text-white"


class GymOperatorForm(forms.ModelForm):
    class Meta:
        model = GymOperator
        fields = ("gym", "user", "is_active")
        labels = {"gym": "باشگاه", "user": "کاربر", "is_active": "اپراتور فعال است"}

    def __init__(self, *args, gym=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.context_gym = gym
        if gym is not None:
            self.fields.pop("gym")
        else:
            self.fields["gym"].empty_label = "باشگاه را انتخاب کنید"
        self.fields["user"].queryset = get_user_model().objects.filter(is_active=True).order_by("first_name", "last_name", "username")
        self.fields["user"].empty_label = "کاربر را انتخاب کنید"
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = SELECT_CLASSES

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.context_gym is not None:
            instance.gym = self.context_gym
        if commit:
            instance.save()
        return instance


class GymContractForm(forms.ModelForm):
    start_date = JalaliDateField(label="تاریخ شروع")
    end_date = JalaliDateField(label="تاریخ پایان")
    price_per_referral = RialDecimalField(max_digits=14, decimal_places=2, label="تعرفه هر معرفی (ریال)", widget=forms.TextInput(attrs={"inputmode": "decimal", "autocomplete": "off", "placeholder": "۱,۵۰۰,۰۰۰"}))

    class Meta:
        model = GymContract
        fields = ("gym", "start_date", "end_date", "price_per_referral", "billing_policy", "is_active")
        labels = {"gym": "باشگاه", "start_date": "تاریخ شروع", "end_date": "تاریخ پایان", "price_per_referral": "تعرفه هر معرفی (ریال)", "billing_policy": "روش صورتحساب", "is_active": "فعال"}

    def __init__(self, *args, gym=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.context_gym = gym
        if gym is not None:
            self.fields.pop("gym")
        for name, field in self.fields.items():
            if name != "is_active":
                field.widget.attrs["class"] = SELECT_CLASSES if isinstance(field.widget, forms.Select) else "w-full bg-white text-gray-900 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
        self.fields["billing_policy"].help_text = "صادرشده: تمام معرفی‌نامه‌های واجد شرایط؛ استفاده‌شده: فقط موارد ثبت‌شده در باشگاه."
        if "gym" in self.fields:
            self.fields["gym"].empty_label = "باشگاه موردنظر را انتخاب کنید"
        self.fields["price_per_referral"].help_text = "مبلغ قابل پرداخت بابت هر معرفی واجد شرایط."

    def clean_price_per_referral(self):
        value = self.cleaned_data["price_per_referral"]
        if value <= 0:
            raise forms.ValidationError("تعرفه باید بزرگ‌تر از صفر باشد.")
        return value

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("start_date"), cleaned.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "تاریخ پایان نمی‌تواند قبل از تاریخ شروع باشد.")
        return cleaned
