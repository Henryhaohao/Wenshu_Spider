# !/user/bin/env python
# -*- coding:utf-8 -*- 
# time: 2018/10/18--17:11
__author__ = 'Henry'


from scrapy import cmdline


if __name__ == '__main__':
    #execute的参数类型为一个列表
    # 写法一
    cmdline.execute('scrapy crawl wenshu'.split())
    # 写法二
    # cmdline.execute(['scrapy', 'crawl', 'wenshu'])