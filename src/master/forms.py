#coding:utf-8
from .models import TestCase
from django import forms
from django.forms.widgets import CheckboxSelectMultiple
from master.models import Plan

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
    testcases = forms.CharField(widget=forms.Textarea)
    description = forms.CharField(required=False, widget=forms.Textarea) 

REPEAT_TYPE_CHOICES = (
    ('1', u'每周一'),
    ('2', u'每周二'),
    ('3', u'每周三'),
    ('4', u'每周四'),
    ('5', u'每周五'),
    ('6', u'每周六'),
    ('7', u'每周日'),
)

class PlanForm(forms.Form):
    test_suite_name = forms.CharField()
    executor = forms.CharField()
    province =forms.CharField()
    city = forms.CharField()
    exectype = forms.CharField()
    hour = forms.CharField(required=False)
    minute = forms.CharField(required=False)
    repeat_type = forms.MultipleChoiceField(required=False, 
                                    widget=CheckboxSelectMultiple(),
                                    choices=REPEAT_TYPE_CHOICES)

class CompatibilityTestScriptForm(forms.Form):
    system = forms.CharField()
    content = forms.CharField(widget=forms.Textarea)