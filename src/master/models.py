#coding:utf-8
from django.db import models

# Create your models here.
class Report(models.Model):
    reporter = models.CharField(u'报告提交人', max_length=100)
    system = models.CharField(u'系统',  max_length=100)
    province = models.CharField(u'省份', max_length=100)
    city = models.CharField(u'城市', max_length=100)
    sub_time = models.DateTimeField(u'提交日期',auto_now=True)
    total_num = models.IntegerField(u'测试用例数目')
    pass_num = models.IntegerField(u'通过测试的数目')
    report_path = models.CharField(u'报告', max_length=100)
    apdex = models.FloatField(u'Apdex')
    browser = models.CharField(u'浏览器', max_length=100)
    
class System(models.Model):
    name = models.CharField(u'系统',  max_length=100)
    english_name = models.CharField(u'系统的英文名称', max_length=100)

class TestCase(models.Model):
    system = models.ForeignKey(System)
    name = models.CharField(u'测试用例名称',  max_length=100)
    content = models.TextField(u'测试用例')
    description = models.TextField(u'测试用例描述')
    
class TestSuite(models.Model):
    system = models.ForeignKey(System)
    name = models.CharField(u'测试套件名称', max_length=100)
    testcases = models.TextField(u'包含的测试套件')
    description = models.TextField(u'测试套件描述')

class Task(models.Model):
    test_suite = models.ForeignKey(TestSuite)
    executor = models.CharField(u'巡检人', max_length=100)
    system = models.ForeignKey(System)
    province = models.CharField(u'省份', max_length=100)
    city = models.CharField(u'城市', max_length=100)
    
class Plan(models.Model):
    task = models.ForeignKey(Task)
    exec_time = models.TimeField()
    repeat_type = models.IntegerField()#以7位二进制数反映重复类型

class CompatibilityScript(models.Model):
    system = models.ForeignKey(System)
    script_path_ie = models.CharField(u'ie的兼容性测试脚本的路径', max_length=200)
    script_path_firefox = models.CharField(u'firefox的兼容性测试脚本的路径', max_length=200)
    script_path_chrome = models.CharField(u'chrome的兼容性测试脚本的路径', max_length=200)