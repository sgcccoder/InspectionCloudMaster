#coding:utf-8
from .forms import ReportForm, TestCaseForm, TestSuiteForm, PlanForm, CompatibilityTestScriptForm
from .models import Report, System, TestCase, Plan, Task, TestSuite, CompatibilityScript
from InspectionCloudMaster import settings
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import F
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import Context, RequestContext
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from master.cluster import Cluster
from master.my_proxy import MyProxy
from master.parser import Parser
import codecs
import datetime
import json
import logging
import os
import re
import time
import zipfile


# Create your views here.

#每页展示的报告数目
REPORT_PER_PAGE = 50

#日志根目录
LOG_ROOT = 'C:\\autoInspectionLog'

#当前时间
current = time.strftime("%Y%m%d%H%M%S",time.localtime(time.time()))

if not os.path.exists(LOG_ROOT):
    os.makedirs(LOG_ROOT)
    
#配置日志
logging.basicConfig(level=logging.INFO,
            format='%(asctime)s:%(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
            datefmt='%a, %d %b %Y %H:%M:%S',
            filename =  LOG_ROOT + os.path.sep + current + '.log',
            filemode='w')

logger = logging.getLogger('Main')

#巡检脚本名称和巡检脚本文件之间的一一映射关系
scripts= {}

#超时时间，单位是秒
timeout = 60

def home(request):
    '''
           应用巡检云服务的主页
    '''
    logger.info(u'访问主页')
    t = get_template('home.html')
    html = t.render(Context())
    return HttpResponse(html)
    
def upload(request):
    '''
         上传巡检报告的页面
    '''
    t = get_template('upload.html')
    html = t.render(Context())
    return HttpResponse(html)

def handle_uploaded_file(f, system, province, reporter):
    '''
            处理巡检人员提交的巡检报告文件
    f表示提交的报告压缩文件
    system表示巡检的系统
    province表示所在的省
    reporter表示提交人员
    '''
    report_path = ""
        #在服务器上创建路径存储巡检人员提交的报告
    try:
        path = settings.MEDIA_ROOT + system + os.path.sep + province + os.path.sep + reporter + time.strftime('\\%Y\\%m\\%d\\%H%M%S\\')
        if not os.path.exists(path):
            os.makedirs(path)
        zip_file = open('report.zip', 'wb+')
        for chunk in f.chunks():
            zip_file.write(chunk)
        zip_file.close()
        zip = zipfile.ZipFile('report.zip')
        for filename in zip.namelist():
            data = zip.read(filename)
            filename = os.path.split(filename)[1]
            file = open(os.path.join(path, filename), 'wb+')
            file.write(data)
            file.close()
            logger.info(filename + u'已上传到服务器' + path)
            if filename == 'report.html':
                logger.info(u'找到report.html')
                report_path = os.path.join(path, filename)
                report_path = report_path.replace(settings.MEDIA_ROOT, '')
                #抽取通过测试的数目和未通过的数目
                pattern = re.compile(r'"fail":\d+,"label":"All Tests","pass":\d+')
                match = pattern.search(data)
                str = match.group()
                nums = re.findall(r'\d+', str)
                fail_num = int(nums[0])
                pass_num = int(nums[1])
                logger.info(u'抽取通过测试的数目和未通过的数目')
            elif filename == 'output.xml':
                logger.info(u'找到output.xml')
                output_xml_path = os.path.join(path, filename)
                parser = Parser(logger)
                apdex_index = parser.calculate_apdex(output_xml_path)

    except Exception, e:
        logger.error(e)
    return report_path, fail_num + pass_num, pass_num, apdex_index


@csrf_exempt
def upload_report(request):
    '''
            完成巡检报告上传工作
    '''    
      
    if request.method == 'POST':
        form = ReportForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            report_info = u'报告人：' + data['reporter'] + u'， 系统：' + data['system'] + u'， 省：' + data['province'] + u'， 市：' + data['city'] 
            logger.info(report_info)
            #获得巡检报告在服务端的存储路径，测试功能点数目，通过的数目
            report_path, total_num, pass_num, apdex = handle_uploaded_file(request.FILES['zip'], data['system'], data['province'], data['reporter'])
            #获得访问巡检报告文件的url
            report_url = default_storage.url(report_path)
            logger.info(u'总测试数目：' + str(total_num)  + u'  通过测试的数目：' + str(pass_num))
            #创建巡检报告实例
            instance = Report(reporter = data['reporter'], system = data['system'], province = data['province'], city = data['city'], total_num = total_num, pass_num = pass_num, report_path = report_url, apdex=apdex)
            instance.save()
            logger.info(u'报告存入数据库')
            return HttpResponseRedirect('/success/')
    else:
        form = ReportForm()
    return render_to_response('upload.html', {'form': form})

def success(request):
    '''
           巡检报告提交成功的页面
    '''
    t = get_template('success.html')
    html = t.render(Context())
    return HttpResponse(html)   

def result(request):
    '''
           巡检报告展示的页面
    '''    
    logger.info(u'查看巡检结果')
    t = get_template('result.html')
    systems = System.objects.all()
    context = {'systems': systems}
    html = t.render(context)
    return HttpResponse(html) 

def search(request):
    '''
           查询巡检报告
    '''      
    q_system = request.REQUEST['system']
    q_reporter = request.REQUEST['reporter']
    q_province = request.REQUEST['province']
    q_city = request.REQUEST['city']
    q_begin_date = request.REQUEST['begin_date']
    q_end_date = request.REQUEST['end_date']
    end_date = datetime.datetime.strptime(q_end_date,'%Y-%m-%d')
    end_date = end_date +  datetime.timedelta(days=1)
    q_end_date = end_date.strftime('%Y-%m-%d')
    q_status = request.REQUEST['status'] 
    report_list = Report.objects.all()
    logger.info(u'获得所有报告')
    if q_system != '':
        report_list = report_list.filter(system=q_system)
    if q_reporter != '':
        report_list = report_list.filter(reporter=q_reporter)
    if q_province != '':
        report_list = report_list.filter(province=q_province)
    if q_city != '':
        report_list = report_list.filter(city=q_city)
    if q_begin_date != '':
        report_list = report_list.filter(sub_time__gte=q_begin_date)
    if q_end_date != '':
        report_list = report_list.filter(sub_time__lt=q_end_date)
    if q_status == 'fail':
        report_list = report_list.exclude(total_num=F('pass_num'))
    if q_status == 'pass':
        report_list = report_list.filter(total_num=F('pass_num'))
    logger.info(u'获得满足查询条件的报告')
    #对查询结果进行排序，先按系统名称的升序排序，然后按照提交日期降序排序。
    report_list = report_list.order_by('-sub_time')
    logger.info(u'对查询结果进行排序')
    #分页
    paginator = Paginator(report_list, REPORT_PER_PAGE)
    page = request.GET.get('page')
    try:
        reports = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        reports = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        reports = paginator.page(paginator.num_pages)

    return render_to_response('report_list_div.html', {"reports": reports})
    logger.info(u'分页')
    

def select_system(request):
    '''
           系统选择页面
    '''  
    systems = System.objects.all()
    context = {'systems': systems}
    t = get_template('select_system.html')
    html = t.render(context)
    return HttpResponse(html)
   
def create_testcase_success(request):
    '''
           测试用例创建成功的提示页面
    '''  
    t = get_template('create_testcase_success.html')
    html = t.render(Context())
    return HttpResponse(html)  

def plan_list(request):
    '''
           巡检计划的展示页面
    '''  
    logger.info(u'查看巡检计划')
    q_system = ''
    try:
       q_system=request.REQUEST['system']
    except:
        q_system = request.COOKIES["system"]
    cur_system_instance = System.objects.get(name=q_system)
    tasks = Task.objects.filter(system=cur_system_instance)
    plans = Plan.objects.filter(task__in=tasks)
    context = {'plans': plans}
    t = get_template('plans.html')
    html = t.render(context)
    response = HttpResponse(html)
    response.set_cookie("system",q_system)
    return response

def add_plan(request):
    '''
           添加巡检计划界面
    '''
    logger.info(u'增加巡检计划')
    cur_system =  request.COOKIES["system"]
    cur_system_instance = System.objects.get(name=cur_system)
    testsuites = TestSuite.objects.filter(system=cur_system_instance)
    hours = range(1,24)
    minutes = range(1, 60)
    context = {'testsuites': testsuites,
               'hours' : hours,
                'minutes' : minutes,
               }
    t = get_template('add_plan.html')
    html = t.render(context)
    return HttpResponse(html)    
 
@csrf_exempt
def create_plan(request):
    '''
          完成巡检计划新增工作
    '''
    if request.method == 'POST':
        form = PlanForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            cur_system =  request.COOKIES["system"]         
            cur_system_instance = System.objects.get(name=cur_system)
            testsuite_instance = TestSuite.objects.get(name=data['test_suite_name'])
            #巡检脚本名称(通过系统实例id和测试套件id保证巡检脚本名称的唯一性)
            script_name = str(cur_system_instance.id) + '-' + str(testsuite_instance.id)
            #巡检脚本路径
            script_path = settings.SCRIPT_ROOT + cur_system_instance.english_name + str(testsuite_instance.id) + '.txt'
            logger.info(u'巡检脚本路径：' + script_path)
            if not os.path.exists(settings.SCRIPT_ROOT):
                os.makedirs(settings.SCRIPT_ROOT)
           
            if script_name not in scripts:
                logger.info(u'新建巡检脚本')
                
                script_str = '*** Settings ***' + os.linesep  \
                + 'Library           Selenium2Library'  + os.linesep  + os.linesep  \
                + '*** Variables ***' + os.linesep \
                + '${timeout}           ' + str(timeout) + os.linesep + os.linesep \
                + '*** Test Cases ***' + os.linesep    
                
                #获得当前系统的所有测试用例
                candidate_test_cases = TestCase.objects.filter(system = cur_system_instance)
                #将testsuite选中的测试用例名称按行分为列表
                testcase_list = testsuite_instance.testcases.split('\n')
                #去除最后一个空行
                testcase_list = testcase_list[:-1]
                
                for testcase_item in testcase_list:
                    #列表中的每一项的格式为'序号 测试用例名称'
                    testcase_name = testcase_item.split(' ')[1]
                    #去除换行符
                    testcase_name = testcase_name.strip('\r')
                    testcase_instance = candidate_test_cases.get(name=testcase_name)
                    script_str = script_str + testcase_instance.name + os.linesep
                    script_str = script_str + testcase_instance.content + os.linesep + os.linesep
                
                script_str = script_str + '    delete all cookies' + os.linesep + \
                                   '    close browser'
                                                               
                f = codecs.open(script_path, 'w', 'utf-8') 
                f.write(script_str)
                f.close()
                scripts[script_name] = script_path
                
            taskinfo = {}
            taskinfo['system'] = cur_system
            taskinfo['executor'] = data['executor']
            taskinfo['province'] = data['province']
            taskinfo['city'] = data['city']
            taskinfo_json = json.dumps(taskinfo)
            para = {'type': 'file'}
            para['path'] = script_path
            para['str'] = taskinfo_json
            para_list = []
            para_list.append(para)
            
            proxy = MyProxy(settings.CLUSTER_MASTER_URL)        
            if data['exectype'] == 'now':
                proxy.add_job('inspect', 'exec', para_list) 
                return HttpResponseRedirect('/createplansuccess1/')
            
            #周期性巡检计划
            task_instance = Task(test_suite = testsuite_instance, 
                                 executor = data['executor'], 
                                 system = cur_system_instance, 
                                 province = data['province'], 
                                 city = data['city'])
            task_instance.save()
            logger.info(u'巡检任务已存入数据库')
            
            hour = int(data['hour'])
            minute = int(data['minute'])
 
            exec_time = datetime.time(hour, minute)

            #用7位二进制数表示重复类型，例如每周一至周五运行，对应的二进制数为（0011111），对应的10进制数为31                       
            repeat_type = 0
            for item in data['repeat_type']:#data['repeat_type']的类型是字符型，范围为1~7
                i = int(item) - 1 #转换为整形，然后将范围调整为0~6
                repeat_type += 2**i
            #创建巡检计划实例                               
            plan_instance = Plan(task = task_instance, exec_time = exec_time, repeat_type = repeat_type)        
            plan_instance.save()  
            proxy.add_plan(hour, minute, repeat_type,'inspect', 'exec', para_list, plan_instance.id)
     
            logger.info(u'巡检计划已存入数据库')
                        
            return HttpResponseRedirect('/createplansuccess2/')
    else:
        form = PlanForm()
    return render_to_response('add_plan.html', {'form': form})

def create_plan_success1(request):
    '''
          创建单次任务成功界面
    '''
    t = get_template('create_plan_success1.html')
    html = t.render(Context())
    return HttpResponse(html)

def create_plan_success2(request):
    '''
          创建周期性计划成功界面
    '''
    t = get_template('create_plan_success2.html')
    html = t.render(Context())
    return HttpResponse(html) 

def testsuite_list(request):
    '''
            查看测试套件
    '''
    cur_system =  request.COOKIES["system"]
    cur_system_instance = System.objects.get(name=cur_system)
    testsuites = TestSuite.objects.filter(system=cur_system_instance)
    t = get_template('testsuites.html')
    context = {'testsuites': testsuites}
    html = t.render(context)
    return HttpResponse(html)

def testsuite_detail(request, testsuite_id):
    '''
            测试套件详细信息
    '''
    testsuite = get_object_or_404(TestSuite, pk=testsuite_id)
    t = get_template('testsuite_detail.html')
    context = {'testsuite': testsuite}
    html = t.render(context)
    return HttpResponse(html)  


def add_testsuite(request):
    '''
           添加测试套件界面
    '''
    cur_system =  request.COOKIES["system"]
    cur_system_instance = System.objects.get(name=cur_system)
    testcases = TestCase.objects.filter(system=cur_system_instance)
    context = {'testcases': testcases}
    t = get_template('add_testsuite.html')
    html = t.render(context)
    return HttpResponse(html)

@csrf_exempt
def create_testsuite(request):
    '''
          完成测试套件新增工作
    '''
    if request.method == 'POST':
        form = TestSuiteForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            cur_system =  request.COOKIES["system"]
            cur_system_instance = System.objects.get(name=cur_system)
            instance = TestSuite(system = cur_system_instance, name = data['name'], testcases=data['testcases'], description = data['description'])
            instance.save()
            logger.info(u'测试套件已存入数据库')
            return HttpResponseRedirect('/createtestsuitesuccess/')
    else:
        form = TestSuiteForm()
    return render_to_response('add_testsuite.html', {'form': form})

def create_testsuite_success(request):
    '''
          测试套件创建成功的页面
    '''  
    t = get_template('create_testsuite_success.html')
    html = t.render(Context())
    return HttpResponse(html)  

def testcase_list(request):
    '''
            查看测试用例列表
    '''
    cur_system =  request.COOKIES["system"]
    cur_system_instance = System.objects.get(name=cur_system)
    testcases = TestCase.objects.filter(system=cur_system_instance)
    t = get_template('testcases.html')
    context = {'testcases': testcases}
    html = t.render(context)
    return HttpResponse(html)

def testcase_detail(request, testcase_id):
    '''
            查看测试用例详细信息
    '''
    testcase = get_object_or_404(TestCase, pk=testcase_id)
    t = get_template('testcase_detail.html')
    context = {'testcase': testcase}
    html = t.render(context)
    return HttpResponse(html)

def add_testcase(request):
    '''
          新增测试用例界面
    '''
    t = get_template('add_testcase.html')
    html = t.render(Context())
    return HttpResponse(html)  

@csrf_exempt
def create_testcase(request):
    '''
          完成测试用例新增工作
    '''
    if request.method == 'POST':
        form = TestCaseForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            cur_system =  request.COOKIES["system"]
            cur_system_instance = System.objects.get(name=cur_system)
            instance = TestCase(system = cur_system_instance, name = data['name'], content = data['content'], description = data['description'])
            instance.save()
            logger.info(u'测试用例已存入数据库')
            return HttpResponseRedirect('/createtestcasesuccess/')
    else:
        form = TestCaseForm()
   
    return render_to_response('add_testcase.html', {'form': form})

def export(request):
    '''
         导出巡检报告
    '''
    response = HttpResponse(content_type='text/plain')                                   
    response['Content-Disposition'] = 'attachment; filename=data.txt'
    report_list = Report.objects.all()
    logger.info(u'获得所有报告')
    parser = Parser(logger)
    i = 1
    seperator = '#'
    for report in report_list:
        pass_rate = float(report.pass_num) / float(report.total_num)
        str_pass_rate = str(int(pass_rate * 100)) + '%'
        #获得巡检报告在服务器的目录
        report_dir = settings.MEDIA_ROOT + report.system + os.path.sep + report.province + os.path.sep + report.reporter
        time_str = os.path.dirname(report.report_path)[-17:]
        time_str.replace('\\',os.path.sep)
        report_dir = report_dir + os.path.sep + time_str
        detail_info = parser.parse_outputxml(report_dir + os.path.sep + 'output.xml')
        if detail_info == '':
        #确少详细信息的记录不导出
            continue
        response.write(str(i) + seperator + report.system + seperator \
                       + report.province + seperator + report.city + seperator \
                       + str(report.total_num) + seperator + str(report.pass_num) + seperator \
                       + str_pass_rate + seperator +  report.sub_time.strftime("%Y-%m-%d") \
                       + seperator + report.reporter + seperator + ' ' + seperator + ' ' + detail_info + seperator)
        i += 1
    return response

def clusterStatus(request):
    '''
          集群状态显示界面
    '''
    t = get_template('cluster_status.html')
    proxy = MyProxy(settings.CLUSTER_MASTER_URL)
    cluster = Cluster(proxy.get_status())
    context = {'nodes': cluster.nodes}
    html = t.render(context)
    return HttpResponse(html)

def add_compatibility_test(request):
    '''
          新增兼容性测试界面
    '''
    systems = System.objects.all()
    context = {'systems': systems}
    t = get_template('add_compatibility_test_script.html')
    html = t.render(context)
    return HttpResponse(html)

@csrf_exempt
def create_compatibility_test_script(request):
    '''

        创建兼容性测试
    '''
    logger.info(u'创建兼容性测试')
    if request.method == 'POST':
        form = CompatibilityTestScriptForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            cur_system = data['system']
            script_content = data['content']
            cur_system_instance = System.objects.get(name=cur_system)
            if not os.path.exists(settings.SCRIPT_ROOT):
                os.makedirs(settings.SCRIPT_ROOT)
            #输入的脚本必须是IE版本
            script_path_ie = settings.SCRIPT_ROOT + cur_system_instance.english_name + '_ie.txt'
            f = codecs.open(script_path_ie, 'w', 'utf-8')
            f.write(script_content)
            f.close()
            logger.info(u'成功创建适用于IE浏览器的兼容性测试脚本文件')

            #找到open browser关键字所在行
            pattern = re.compile(r'.*open browser.*ie')
            match = pattern.search(script_content)
            open_browser_by_ie = ''
            if match:
                open_browser_by_ie = match.group(0)
            else:
                logger.error(u'未找到open browser关键字')

            #创建FIERFOX版本的脚本
            open_browser_by_firefox = open_browser_by_ie[:-3]
            print open_browser_by_firefox
            script_content_firefox = script_content.replace(open_browser_by_ie, open_browser_by_firefox)
            script_path_firefox = settings.SCRIPT_ROOT + cur_system_instance.english_name + '_firefox.txt'
            f = codecs.open(script_path_firefox, 'w', 'utf-8')
            f.write(script_content_firefox)
            f.close()
            logger.info(u'成功创建适用于FIREFOX浏览器的兼容性测试脚本文件')

            #创建CHROME版本的脚本
            open_browser_by_chrome = open_browser_by_firefox + 'chrome'
            script_content_chrome = script_content.replace(open_browser_by_ie, open_browser_by_chrome)
            script_path_chrome = settings.SCRIPT_ROOT + cur_system_instance.english_name + '_chrome.txt'
            f = codecs.open(script_path_chrome, 'w', 'utf-8')
            f.write(script_content_chrome)
            f.close()
            logger.info(u'成功创建适用于CHROME浏览器的兼容性测试脚本文件')

            compatiblity_script_instance = CompatibilityScript(system = cur_system_instance, script_path_ie = script_path_ie, script_path_firefox = script_path_firefox, script_path_chrome = script_path_chrome)
            compatiblity_script_instance.save()
            logger.info(u'兼容性测试脚本已存入数据库')
            return HttpResponseRedirect('/createcompatiblitytestscriptsuccess/')
    else:
        form = CompatibilityTestScriptForm()
    return render_to_response('add_compatibility_test_script.html', {'form': form})

def create_compatibility_test_script_success(request):
    '''
           巡检报告提交成功的页面
    '''
    t = get_template('create_compatibility_test_script_success.html')
    html = t.render(Context())
    return HttpResponse(html)

def create_compatibility_test_task(request):
    '''
           兼容性选择系统
    '''
    logger.info(u'兼容性选择系统')
    systems = System.objects.all()
    context = {'systems': systems}
    t = get_template('create_compatibility_test_task.html')
    html = t.render(context)
    return HttpResponse(html)

def compatibility_test(request):
    '''
    兼容性测试
    '''
    logger.info(u'开始兼容性测试')
    if request.method == 'POST':
        form = PlanForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            cur_system = data['system']
            cur_system_instance = System.objects.get(name=cur_system)
            compatibility_script_instance = CompatibilityScript.objects.get(system = cur_system_instance)
            proxy = MyProxy(settings.CLUSTER_MASTER_URL)

            taskinfo_ie8 = {}
            taskinfo_ie8['system'] = cur_system
            taskinfo_ie8['executor'] = data['executor']
            taskinfo_ie8['province'] = data['province']
            taskinfo_ie8['city'] = data['city']
            taskinfo_ie8_json = json.dumps(taskinfo_ie8)
            para_ie8 = {'type': 'file'}
            para_ie8['path'] = compatibility_script_instance.script_ie_path
            para_ie8['str'] = taskinfo_ie8_json
            para_list_ie8 = []
            para_list_ie8.append(para_ie8)
            proxy.add_job_with_type('inspect', 'IE8', 'exec', para_list_ie8)

            taskinfo_ie10 = {}
            taskinfo_ie10['system'] = cur_system
            taskinfo_ie10['executor'] = data['executor']
            taskinfo_ie10['province'] = data['province']
            taskinfo_ie10['city'] = data['city']
            taskinfo_ie10_json = json.dumps(taskinfo_ie10)
            para_ie10 = {'type': 'file'}
            para_ie10['path'] = compatibility_script_instance.script_ie_path
            para_ie10['str'] = taskinfo_ie10_json
            para_list_ie10 = []
            para_list_ie10.append(para_ie10)
            proxy.add_job_with_type('inspect', 'IE10', 'exec', para_list_ie10)

            taskinfo_fx = {}
            taskinfo_fx['system'] = cur_system
            taskinfo_fx['executor'] = data['executor']
            taskinfo_fx['province'] = data['province']
            taskinfo_fx['city'] = data['city']
            taskinfo_fx_json = json.dumps(taskinfo_fx)
            para_fx = {'type': 'file'}
            para_fx['path'] = compatibility_script_instance.script_firefox_path
            para_fx['str'] = taskinfo_fx_json
            para_list_fx = []
            para_list_fx.append(para_fx)
            proxy = MyProxy(settings.CLUSTER_MASTER_URL)
            proxy.add_job_with_type('inspect', 'FX', 'exec', para_list_fx)

            taskinfo_chrome = {}
            taskinfo_chrome['system'] = cur_system
            taskinfo_chrome['executor'] = data['executor']
            taskinfo_chrome['province'] = data['province']
            taskinfo_chrome['city'] = data['city']
            taskinfo_chrome_json = json.dumps(taskinfo_chrome)
            para_chrome = {'type': 'file'}
            para_chrome['path'] = compatibility_script_instance.script_chrome_path
            para_chrome['str'] = taskinfo_chrome_json
            para_chrome_list = []
            para_chrome_list.append(para_chrome)
            proxy.add_job_with_type('inspect', 'CHROME', 'exec', para_chrome_list)
            return HttpResponseRedirect('/result/')




