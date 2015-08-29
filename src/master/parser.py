#coding:utf-8
from xml.etree import ElementTree as ET  
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
            detail_info = '巡检开始时间 '+ starttime + '\\n' + '巡检结束时间 ' + endtime

            #获得所有测试用例
            tests = suite.findall('test')
            for test in tests:
                detail_info += '\\n'
                detail_info += test.attrib['name']
                detail_info += ' '
                #获得测试用例状态
                teststatus = test.find('status').attrib['status']
                #英译汉
                if teststatus == 'PASS':
                    detail_info += u'通过'
                else:
                    detail_info += u'未通过'
        except Exception, e:  
            self.logger.error("Error: cannot parse file: " + file_path )

        print detail_info
        return detail_info 