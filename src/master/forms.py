from django import forms
from .models import TestCase

class ReportForm(forms.Form):
    system = forms.CharField()
    province = forms.CharField()
    city = forms.CharField()
    reporter = forms.CharField()
    zip = forms.FileField()
    
class TestCaseForm(forms.Form):
    name = forms.CharField()
    content = forms.CharField(widget=forms.Textarea)
    description = forms.CharField(required=False, widget=forms.Textarea)

class TestSuiteForm(forms.Form):
    name = forms.CharField()
    test_cases = forms.ModelMultipleChoiceField(queryset=TestCase.objects.all())
    description = forms.CharField(required=False, widget=forms.Textarea)   