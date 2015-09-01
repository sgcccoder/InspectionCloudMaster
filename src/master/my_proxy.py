#from apscheduler.schedulers.background import BackgroundScheduler
import os
import time
import xmlrpclib

#sched = BackgroundScheduler()
#sched.start()

class MyProxy:
    def __init__(self, master_url):
        print master_url
        self.master_proxy = xmlrpclib.ServerProxy(master_url)
    
    def add_job(self, job_name, job_cmd,  para_list):
        self.master_proxy.add_job_by_para(job_name, job_cmd, para_list)
    
    def add_plan(self, job_name, job_cmd,  para_list, h, m, repeat_type, plan_id):
#        str_day_of_week = ','.join(repeat_type)
#        str_day_of_week.replace('7', '0')
#        str_day_of_week = '1,2,3,4,5'
#        sched.add_job(self.add_job, args=[job_name, job_cmd, para_list ], id = plan_id, trigger='cron',  day_of_week=str_day_of_week, hour=h, minute=m)
        print 'add plan success'
    
#    def remove_plan(self, plan_id):
#        sched.remove_job(plan_id)
        
