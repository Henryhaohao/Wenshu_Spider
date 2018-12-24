# -*- coding: utf-8 -*-
import scrapy, time, json, re, math, execjs
from Wenshu.items import WenshuCaseItem


class WenshuSpider(scrapy.Spider):
    name = 'wenshu'
    # allowed_domains = ['wenshu.court.gov.cn']
    start_urls = ['http://wenshu.court.gov.cn/list/list/?sorttype=1']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.year_list = ['1996', '1997', '1998', '1999', '2000']
        self.guid = 'aaaabbbb-aaaa-aaaabbbb-aaaabbbbcccc'
        with open('Wenshu\spiders\get_vl5x.js', encoding='utf-8') as f:
            jsdata_1 = f.read()
        with open('Wenshu\spiders\get_docid.js', encoding='utf-8') as f:
            jsdata_2 = f.read()
        self.js_1 = execjs.compile(jsdata_1)
        self.js_2 = execjs.compile(jsdata_2)

    def parse(self, response):
        '''获取cookie'''
        try:
            vjkl5 = response.headers['Set-Cookie'].decode('utf-8')
            vjkl5 = vjkl5.split(';')[0].split('=')[1]
            url_num = 'http://wenshu.court.gov.cn/ValiCode/GetCode'
            data = {
                'guid': self.guid
            }
            yield scrapy.FormRequest(url_num, formdata=data, meta={'vjkl5': vjkl5}, callback=self.get_count,
                                     dont_filter=True)
        except:
            yield scrapy.Request(WenshuSpider.start_urls, callback=self.parse, dont_filter=True)

    def get_count(self, response):
        '''获取案件数目,设置请求页数'''
        number = response.text
        vjkl5 = response.meta['vjkl5']
        vl5x = self.js_1.call('getvl5x', vjkl5)
        url = 'http://wenshu.court.gov.cn/List/ListContent'
        for year in self.year_list:
            data = {
                'Param': '裁判年份:{}'.format(year),  # 检索筛选条件 (多条件筛选: 裁判年份:2018,中级法院:北京市第一中级人民法院,审判程序:一审,关键词:返还)
                'Index': '1',  # 页数
                'Page': '0',  # 只为了获取案件数目,所有请求0条就行了
                'Order': '裁判日期',  # 排序类型(1.法院层级/2.裁判日期/3.审判程序)
                'Direction': 'asc',  # 排序方式(1.asc:从小到大/2.desc:从大到小)
                'vl5x': vl5x,
                'number': number,
                'guid': self.guid
            }
            headers = {
                'Cookie': 'vjkl5=' + response.meta['vjkl5'],  # 在这单独添加cookie,settings中就可以禁用cookie,防止跟踪被ban
                'Host': 'wenshu.court.gov.cn',
                'Origin': 'http://wenshu.court.gov.cn',
            }
            # print(response.request.headers.getlist('Cookie'))
            yield scrapy.FormRequest(url, formdata=data,
                                     meta={'vl5x': vl5x, 'vjkl5': vjkl5, 'number': number, 'year': year},
                                     callback=self.get_content, headers=headers, dont_filter=True)

    def get_content(self, response):
        '''获取每页的案件'''
        html = response.text
        result = eval(json.loads(html))
        count = result[0]['Count']
        print('******* {}年:该筛选条件下共有多少条数据:{} ********'.format(response.meta['year'], count))
        page = math.ceil(int(count) / 10)  # 向上取整,每页10条
        for i in range(1, int(page) + 1):
            if i <= 20:  # max:10*20=200 ; 20181005 -只能爬取20页,每页10条!!!
                url = 'http://wenshu.court.gov.cn/List/ListContent'
                data = {
                    'Param': '裁判年份:{}'.format(response.meta['year']),
                    # 检索筛选条件 (多条件筛选: 裁判年份:2018,中级法院:北京市第一中级人民法院,审判程序:一审,关键词:返还)
                    'Index': str(i),  # 页数
                    'Page': '10',  # 每页显示的条目数
                    'Order': '裁判日期',  # 排序类型(1.法院层级/2.裁判日期/3.审判程序)
                    'Direction': 'asc',  # 排序方式(1.asc:从小到大/2.desc:从大到小)
                    'vl5x': response.meta['vl5x'],  # 保存1个小时
                    'number': response.meta['number'],  # 每次都要请求一次GetCode,获取number带入
                    'guid': self.guid
                }
                headers = {
                    'Cookie': 'vjkl5=' + response.meta['vjkl5'],
                    'Host': 'wenshu.court.gov.cn',
                    'Origin': 'http://wenshu.court.gov.cn',
                }
                yield scrapy.FormRequest(url, formdata=data, callback=self.get_docid, headers=headers, dont_filter=True)

    def get_docid(self, response):
        '''计算出docid'''
        html = response.text
        result = eval(json.loads(html))
        runeval = result[0]['RunEval']
        content = result[1:]
        for i in content:
            casewenshuid = i.get('文书ID', '')
            casejudgedate = i.get('裁判日期', '')
            docid = self.js_2.call('getdocid', runeval, casewenshuid)
            print('*************文书ID:' + docid)
            url = 'http://wenshu.court.gov.cn/CreateContentJS/CreateContentJS.aspx?DocID={}'.format(docid)
            yield scrapy.Request(url, callback=self.get_detail, meta={'casejudgedate':casejudgedate}, dont_filter=True)

    def get_detail(self, response):
        '''获取每条案件详情'''
        html = response.text
        content_1 = json.loads(re.search(r'JSON\.stringify\((.*?)\);\$\(document', html).group(1))  # 内容详情字典1
        content_3 = re.search(r'"Html\\":\\"(.*?)\\"}"', html).group(1)  # 内容详情字典3(doc文档正文)
        reg = re.compile(r'<[^>]+>', re.S)
        # 存储到item
        item = WenshuCaseItem()
        item['casecourt'] = {
            'casecourtid': content_1.get('法院ID', ''),
            'casecourtname': content_1.get('法院名称', ''),
            'casecourtprovince': content_1.get('法院省份', ''),
            'casecourtcity': content_1.get('法院地市', ''),
            'casecourtdistrict': content_1.get('法院区县', ''),
            'casecourtarea': content_1.get('法院区域', ''),
        }
        item['casecontent'] = {
            'casebasecontent': content_1.get('案件基本情况段原文', ''),
            'caseaddcontent': content_1.get('附加原文', ''),
            'caseheadcontent': content_1.get('文本首部段落原文', ''),
            'casemaincontent': content_1.get('裁判要旨段原文', ''),
            'casecorrectionscontent': content_1.get('补正文书', ''),
            'casedoccontent': content_1.get('DocContent', ''),
            'caselitigationcontent': content_1.get('诉讼记录段原文', ''),
            'casepartycontent': content_1.get('诉讼参与人信息部分原文', ''),
            'casetailcontent': content_1.get('文本尾部原文', ''),
            'caseresultcontent': content_1.get('判决结果段原文', ''),
            'casestrcontent': reg.sub('', content_3),  # 去除html标签后的文书内容
        }
        item['casetype'] = content_1.get('案件类型', '')  # 案件类型
        item['casejudgedate'] = response.meta['casejudgedate']  # 裁判日期
        item['caseprocedure'] = content_1.get('审判程序', '')
        item['casenumber'] = content_1.get('案号', '')
        item['casenopublicreason'] = content_1.get('不公开理由', '')
        item['casedocid'] = content_1.get('文书ID', '')
        item['casename'] = content_1.get('案件名称', '')
        item['casecontenttype'] = content_1.get('文书全文类型', '')
        item['caseuploaddate'] = time.strftime("%Y-%m-%d",
                                               time.localtime(int(content_1['上传日期'][6:-5]))) if 'Date' in content_1[
            '上传日期'] else ''
        item['casedoctype'] = content_1.get('案件名称').split('书')[0][-2:] if '书' in content_1.get(
            '案件名称') else '令'  # 案件文书类型:判决或者裁定...还有令
        item['caseclosemethod'] = content_1.get('结案方式', '')
        item['caseeffectivelevel'] = content_1.get('效力层级', '')

        yield item
