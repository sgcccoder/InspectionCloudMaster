#coding:utf-8
import os
import time
import xmlrpclib


class MyProxy:
    def __init__(self, master_url):
        print master_url
        self.master_proxy = xmlrpclib.ServerProxy(master_url,allow_none=True)
    
    def add_job(self, job_name, job_cmd,  para_list):
        self.master_proxy.add_job_by_para(job_name, job_cmd, para_list)
    
    def add_plan(self, h, m, repeat_type, job_name, job_cmd,  para_list, plan_id):
        self.master_proxy.add_schedule(h, m, repeat_type, job_name, job_cmd, para_list)
        #print 'add plan success'
    
#    def remove_plan(self, plan_id):
#        sched.remove_job(plan_id)

    def get_status(self):
        return self.master_proxy.get_slave_list()
        
