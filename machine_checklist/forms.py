from django import forms
from .models import CheckList, CheckListItem, CheckListTemplate

class CheckListForm(forms.ModelForm):
    class Meta:
        model = CheckList
        fields = ['mining_machine', 'working_hours', 'is_suitable',
                  'operator_signature', 'receiver_signature',
                  'repair_manager_signature', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
class CheckListTemplateForm(forms.ModelForm):
    class Meta:
        model = CheckListTemplate
        fields = '__all__'

class CheckListItemForm(forms.ModelForm):
    class Meta:
        model = CheckListItem
        fields = ['is_suitable', 'description', 'template']
        widgets = {
              'description': forms.Textarea(attrs={'rows': 2}),
              'template': forms.HiddenInput(),
         }


CheckListItemFormSet = forms.inlineformset_factory(
    CheckList,
    CheckListItem,
    form=CheckListItemForm,
    extra=0,
    can_delete=False,
    )