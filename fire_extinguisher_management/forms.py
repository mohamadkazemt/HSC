from django import forms
from .models import FireExtinguisherType, FireExtinguisher, ServiceRecord
from django.contrib.contenttypes.models import ContentType

class FireExtinguisherTypeForm(forms.ModelForm):
    class Meta:
        model = FireExtinguisherType
        fields = '__all__'
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class FireExtinguisherForm(forms.ModelForm):
    class Meta:
        model = FireExtinguisher
        fields = '__all__'
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'replacement_notes': forms.Textarea(attrs={'rows': 3}),
            'last_service_date': forms.DateInput(attrs={'class': 'jalali-datepicker'}),
            'next_service_date': forms.DateInput(attrs={'class': 'jalali-datepicker'}),
        }

class ServiceRecordForm(forms.ModelForm):
    class Meta:
        model = ServiceRecord
        fields = '__all__'
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'actions_taken': forms.Textarea(attrs={'rows': 3}),
            'service_date': forms.DateInput(attrs={'class': 'jalali-datepicker'}),
        }

class FireExtinguisherReplacementForm(forms.Form):
    old_extinguisher = forms.ModelChoiceField(
        queryset=FireExtinguisher.objects.filter(status='OPERATIONAL'),
        label="کپسول قدیمی"
    )
    new_extinguisher = forms.ModelChoiceField(
        queryset=FireExtinguisher.objects.filter(status='RESERVED'),
        label="کپسول جدید"
    )
    replacement_notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label="توضیحات جایگزینی"
    )

class FireExtinguisherLocationForm(forms.Form):
    location_type = forms.ChoiceField(
        choices=[
            ('section', 'بخش'),
            ('machine', 'دستگاه')
        ],
        label="نوع مکان"
    )
    location_section = forms.ModelChoiceField(
        queryset=ContentType.objects.get(model='locationsection').model_class().objects.all(),
        required=False,
        label="بخش"
    )
    location_machine = forms.ModelChoiceField(
        queryset=ContentType.objects.get(model='miningmachine').model_class().objects.all(),
        required=False,
        label="دستگاه"
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label="توضیحات تغییر مکان"
    )

    def clean(self):
        cleaned_data = super().clean()
        location_type = cleaned_data.get('location_type')
        location_section = cleaned_data.get('location_section')
        location_machine = cleaned_data.get('location_machine')

        if location_type == 'section' and not location_section:
            raise forms.ValidationError("برای مکان از نوع بخش، باید بخش را انتخاب کنید.")
        if location_type == 'machine' and not location_machine:
            raise forms.ValidationError("برای مکان از نوع دستگاه، باید دستگاه را انتخاب کنید.")
        if location_type == 'section' and location_machine:
            raise forms.ValidationError("برای مکان از نوع بخش، نمی‌توانید دستگاه انتخاب کنید.")
        if location_type == 'machine' and location_section:
            raise forms.ValidationError("برای مکان از نوع دستگاه، نمی‌توانید بخش انتخاب کنید.")

        return cleaned_data 