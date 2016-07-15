#coding:utf-8
from xml.etree import ElementTree as ET
import datetime
class Parser:
    def __init__(self, logger):
        self.logger = logger
        
    def parse_outputxml(self, file_path):
        '''
                    解析robotframework生成的output.xml，获得测试报告的详细信息
        '''
        detail_info = ''
        try:  
            tree = ET.parse(file_path) #打开xml文档  
            root = tree.getroot() #获得root节点  
            #获得suite节点
            suite = root.find('suite')
            suitestatus = suite.find('status')
            #获得巡检开始时间
            starttime = suitestatus.attrib['starttime']
            #调整精度到秒
            starttime = starttime.split('.')[0]
            #获得巡检结束时间
            endtime = suitestatus.attrib['endtime']
            #调整精度到秒
            endtime = endtime.split('.')[0]
            detail_info = u'巡检开始时间 '+ starttime + '\\n' + u'巡检结束时间 ' + endtime

            #获得所有测试用例
            tests = suite.findall('test')
            i = 1 #序号
            for test in tests:
                detail_info += '\\n'
                detail_info += str(i)
                detail_info += ' '
                detail_info += test.attrib['name']
                detail_info += ' '
                #获得测试用例状态
                teststatus = test.find('status').attrib['status']
                #英译汉
                if teststatus == 'PASS':
                    detail_info += u'通过'
                else:
                    detail_info += u'未通过'
                i += 1
        except Exception, e:  
            self.logger.error("Error: cannot parse file: " + file_path )

        return detail_info

    def calculate_apdex(self, file_path):
        '''
           计算Apdex指数
        '''
        T1 = 3
        T2 = T1 * 4
        satisfy_num = 0
        tolerant_num = 0
        total_num = 0
        try:
            tree = ET.parse(file_path) #打开xml文档
            root = tree.getroot() #获得root节点
            #获得suite节点
            suite = root.find('suite')
            #获得所有测试用例
            tests = suite.findall('test')
            i = 1 #序号
            for test in tests:
                #获得所有关键字
                keywords = test.findall('kw')
                for keyword in keywords:
                    keyword_status = keyword.find('status')
                    #获得关键字开始时间
                    starttime_str = keyword_status.attrib['starttime']
                    #获得关键字结束时间
                    endtime_str = keyword_status.attrib['endtime']

                    starttime = datetime.datetime.strptime(starttime_str, "%Y%m%d %H:%M:%S.%f")
                    endtime =  datetime.datetime.strptime(endtime_str, "%Y%m%d %H:%M:%S.%f")
                    duration_time = (endtime - starttime).seconds
                    print duration_time
                    if duration_time <= T1:
                        satisfy_num += 1
                    elif duration_time <= T2:
                        tolerant_num += 1

                    total_num += 1

            apdex_index = (satisfy_num + tolerant_num * 0.5) / total_num
            self.logger.info('apdex :' + apdex_index)

        except Exception, e:
            self.logger.error("Error: cannot parse file: " + file_path)

        return apdex_index
