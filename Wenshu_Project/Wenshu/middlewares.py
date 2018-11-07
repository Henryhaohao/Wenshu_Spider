# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
import random, requests, logging, base64


class RandomUserAgentMiddleware(object):
    def __init__(self, agents):
        self.agents = agents

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings.getlist('USER_AGENTS'))

    def process_request(self, request, spider):
        # print("********Current UserAgent********" + random.choice(self.agents))
        request.headers.setdefault('User-Agent', random.choice(self.agents))


# 法一:连接阿布云动态代理隧道(付费:IP质量好)
class ProxyMiddleware(object):
    def __init__(self):
        # 阿布云代理服务器
        self.proxyServer = "http://http-dyn.abuyun.com:9020"
        # 代理隧道验证信息
        proxyUser = "***在此填入阿布云通行证书***"
        proxyPass = "***在此填入阿布云通行密钥***"
        self.proxyAuth = "Basic " + base64.urlsafe_b64encode(bytes((proxyUser + ":" + proxyPass), "ascii")).decode("utf8") # Python3
        # self.proxyAuth = "Basic " + base64.b64encode(proxyUser + ":" + proxyPass) # Python2

    def process_request(self, request, spider):
        '''处理请求request'''
        request.headers['Proxy-Authorization'] = self.proxyAuth
        request.meta['proxy'] = self.proxyServer

    def process_response(self, request, response, spider):
        '''处理返回的response'''
        # print(response.url)
        html = response.body.decode()
        if response.status != 200 or 'remind key' in html or 'remind' in html or '请开启JavaScript' in html or '服务不可用' in html:
            print('正在重新请求************')
            new_request = request.copy()
            new_request.dont_filter = True
            return new_request
        else:
            return response

    def process_exception(self, request, exception, spider):
        new_request = request.copy()
        new_request.dont_filter = True
        return new_request


# 法二:连接本地自己维护的代理池(免费:但是IP质量不好,很容易被ban掉)
# class ProxyMiddleware(object):
#     def __init__(self, PROXY_POOL_URL, DELETE_PROXY_URL):
#
#     # self.PROXY_POOL_URL = PROXY_POOL_URL
#     # self.DELETE_PROXY_URL = DELETE_PROXY_URL
#
#     @classmethod
#     def from_crawler(cls, crawler):
#         return cls(
#             crawler.settings.get('PROXY_POOL_URL'),
#             crawler.settings.get('DELETE_PROXY_URL')
#         )
#
#     def process_request(self, request, spider):
#         '''处理请求request'''
#         # request.meta['proxy'] = 'http://' + self.get_randomproxy()
#
#     def process_response(self, request, response, spider):
#         '''处理返回的response'''
#         # if response.status != 200 or response.body in ['"remind key"', 'remind'] or '请开启JavaScript' in response.body:
#         print(response.url)
#         # print(response.body)
#
#         # if response.status != 200 or b'remind' in response.body or b"[]" in response.body or b"window.location.href" in response.body:
#         # # if response.status != 200 or 'VisitRemind' in response.url: # 'VisitRemind' in response.url:出现一级验证码
#         #     print('请求太快,该IP已被封禁...尝试切换新的IP...')
#         #     if 'proxy' in request.meta :
#         #         # print(request.meta['proxy'])
#         #         self.delete_proxy(request.meta['proxy'].split('//')[1]) # 请求失败,删除此IP
#         #     proxy = self.get_randomproxy()
#         #     print("********Current Proxy********" + str(proxy))
#         #     request.meta['proxy'] = 'http://' + proxy # 切换新IP重新请求
#         #     return request
#         return response
#
#     def get_randomproxy(self):
#         '''随机从IP池中获取代理'''
#         try:
#             response = requests.get(self.PROXY_POOL_URL)
#             if response.status_code == 200:
#                 return response.text
#         except:
#             # return None
#             return self.get_randomproxy()
#
#     def delete_proxy(self, proxy):
#         '''请求失败,从代理池中删除此IP'''
#         try:
#             response = requests.get(self.DELETE_PROXY_URL + proxy)
#             if response.text == 1:
#                 logging.info('删除IP成功')
#                 print('删除IP成功')
#         except:
#             logging.info('删除IP失败')
#             print('删除IP失败')


class WenshuSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class WenshuDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
