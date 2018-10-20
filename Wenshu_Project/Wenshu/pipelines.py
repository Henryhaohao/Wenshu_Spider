# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo,time
from pymongo.errors import DuplicateKeyError
from scrapy.conf import settings


# 1.简单同步存储item
class WenshuPipeline(object):
    def __init__(self):
        host = settings['MONGODB_HOST']
        port = settings['MONGODB_PORT']
        dbname = settings['MONGODB_DBNAME']
        docname = settings['MONGODB_DOCNAME']
        self.client = pymongo.MongoClient(host=host,port=port)
        db = self.client[dbname]
        db[docname].ensure_index('casedocid', unique=True)  # 设置文书ID为唯一索引,避免插入重复数据
        self.post = db[docname]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        '''插入数据'''
        try:
            data = dict(item)
            self.post.insert_one(data)
            return item
        except DuplicateKeyError:
            # 索引相同,即为重复数据,捕获错误
            spider.logger.debug('Duplicate key error collection')
            return item


# 2.异步存储item - 不行!插入不了数据! (参考:https://zhuanlan.zhihu.com/p/44003499)
# from twisted.internet import defer, reactor
# class WenshuPipeline(object):
#     def __init__(self, mongo_host, mongo_port, mongo_db, mongo_doc):
#         self.mongo_host = mongo_host
#         self.mongo_port = mongo_port
#         self.mongo_db = mongo_db
#         self.mongo_doc = mongo_doc
#
#     @classmethod
#     def from_crawler(cls, crawler):
#         return cls(
#             mongo_host=crawler.settings.get('MONGODB_HOST'),
#             mongo_port=crawler.settings.get('MONGODB_PORT'),
#             mongo_db=crawler.settings.get('MONGODB_DBNAME'),
#             mongo_doc=crawler.settings.get('MONGODB_DOCNAME'),
#         )
#
#     def open_spider(self, spider):
#         self.client = pymongo.MongoClient(host=self.mongo_host,port=self.mongo_port)
#         self.mongodb = self.client[self.mongo_db]
#         self.mongodb[self.mongo_doc].create_index('id', unique=True) # 创建索引,避免插入数据
#
#     def close_spider(self, spider):
#         self.client.close()
#
#     # 下面的操作是重点
#     @defer.inlineCallbacks
#     def process_item(self, item, spider):
#         out = defer.Deferred()
#         reactor.callInThread(self._insert, item, out, spider)
#         yield out
#         defer.returnValue(item)
#         return item
#
#     def _insert(self, item, out, spider):
#         time.sleep(10)
#         try:
#             self.mongodb[self.mongo_doc].insert_one(dict(item))
#             reactor.callFromThread(out.callback, item)
#         except DuplicateKeyError:
#             # 索引相同,即为重复数据,捕获错误
#             spider.logger.debug('duplicate key error collection')
#             reactor.callFromThread(out.callback, item)