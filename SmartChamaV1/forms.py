from django import forms
from .models import ChamaMember

class MemberForm(forms.ModelForm):
    confirm_password=forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model=ChamaMember
        fields=['full_name', 'email','phone_number','idNumber','password'] 
        widgets={ 'password': forms.PasswordInput()}

    def clean(self):
        cleaned_data= super().clean()
        password=cleaned_data.get("password")
        confirm_password=cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match!!")    