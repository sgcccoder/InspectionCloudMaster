#coding:utf-8
from django import template

register = template.Library()

@register.filter
def display_repeat_type(repeat_type):
    '''
          根据repeat_type的二进制表示输出重复类型
    '''
    alist = ['每周一', '每周二', '每周三', '每周四', '每周五', '每周六', '每周日']
    i = 0
    description = ''
    while repeat_type:
        if repeat_type % 2 == 1 :
            if description != '' :
                description += '，'
            description += alist[i]
        repeat_type /= 2
        i += 1
    return description

@register.filter
def english_to_chinese(input_str):
    '''
          英译汉
    '''
    my_dict = {'idle' : '空闲', 'busy': '忙碌', 'unavailable': '不可达', 'stopped': '已停止'}
    return my_dict[input_str] 
    