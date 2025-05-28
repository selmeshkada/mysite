from django import forms
from .models import Application, Document

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['auditor_company', 'file', 'audit_start', 'audit_end', 'comments']
        widgets = {
            'audit_start': forms.DateInput(attrs={'type': 'date'}),
            'audit_end': forms.DateInput(attrs={'type': 'date'}),
            'comments': forms.Textarea(attrs={'rows': 3}),
        }

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['name', 'type', 'file']