# -*- coding: utf-8 -*-
# @Time    : 2022/10/22 17:31
# @Author  : Liuyijie
# @File    : cnki_oversea.py
# -*- coding: utf-8 -*-
import asyncio
import json
import math
import time
# import requests
import aiohttp
import aiofiles
from hidmiddleware import middleware
from collections import Counter
from urllib.parse import unquote
from lxml import etree
from Yjsdl import Spider, item
from copy import deepcopy


# 请求参数
def generate_search_param(QueryJson, en_id, page: int = None, sort: str = 'desc'):
    page = page or 1

    # 第一页issearch为true
    search_param = {
        'IsSearch': True if page == 1 else False,
        'QueryJson': json.dumps(QueryJson, ensure_ascii=False),
        # 'SearchSql': sql,
        'PageName': 'AdvSearch',
        'HandlerId': 0,
        # CFLQ 学术期刊 CDMD 论文 CFLP 会议 CCND 报纸 SNAD 成果 WBFD 中文图书
        'DBCode': en_id,
        'KuaKuCodes': '',
        'CurPage': page,
        'RecordsCntPerPage': 50,
        'CurDisplayMode': 'listmode',
        'CurrSortField': 'PT',
        'CurrSortFieldType': sort,
        'IsSortSearch': False,
        'IsSentenceSearch': False,
        'Subject': '',
    }
    return search_param


# 请求参数
def generate_muti_group(en_id, sub_name, year):
    # QueryJson = {"Platform": "", "DBCode": en_id, "KuaKuCode": "", "QNode": {"QGroup": [
    #     {"Key": "Subject", "Title": "", "Logic": 4, "Items": [], "ChildItems": [
    #         {"Key": "input[data-tipid=gradetxt-1]", "Title": "Chinese Library Classification", "Logic": 0, "Items": [
    #             {"Key": "", "Title": sub_name, "Logic": 1, "Name": "CLC", "Operate": "=", "Value": sub_name,
    #              "ExtendType": 1,
    #              "ExtendValue": "中英文对照", "Value2": "", "BlurType": "??"}], "ChildItems": []}]},
    #     {"Key": "ControlGroup", "Title": "", "Logic": 1, "Items": [], "ChildItems": []},
    #     {"Key": "MutiGroup", "Title": "", "Logic": 1, "Items": [], "ChildItems": [{"Key": "3", "Title": "", "Logic": 1,
    #                                                                                "Items": [
    #                                                                                    {"Key": year, "Title": year,
    #                                                                                     "Logic": 2, "Name": "年",
    #                                                                                     "Operate": "", "Value": year,
    #                                                                                     "ExtendType": 0,
    #                                                                                     "ExtendValue": "", "Value2": "",
    #                                                                                     "BlurType": ""}],
    #                                                                                "ChildItems": []}]}]},
    #              "CodeLang": ""}

    QueryJson = {"Platform": "", "DBCode": en_id, "KuaKuCode": "", "QNode": {"QGroup": [
        {"Key": "Subject", "Title": "", "Logic": 4, "Items": [], "ChildItems": [
            {"Key": "input[data-tipid=gradetxt-1]", "Title": "Chinese Library Classification", "Logic": 0, "Items": [
                {"Key": "", "Title": sub_name, "Logic": 1, "Name": "CLC", "Operate": "=", "Value": sub_name, "ExtendType": 1,
                 "ExtendValue": "中英文对照", "Value2": "", "BlurType": "??"}], "ChildItems": []}]},
        {"Key": "ControlGroup", "Title": "", "Logic": 1, "Items": [], "ChildItems": [
            {"Key": ".tit-startend-yearbox", "Title": "", "Logic": 1, "Items": [
                {"Key": ".tit-startend-yearbox", "Title": "Publication Year", "Logic": 1, "Name": "YE", "Operate": "",
                 "Value": year, "ExtendType": 2, "ExtendValue": "", "Value2": year, "BlurType": ""}],
             "ChildItems": []}]},
        {"Key": "MutiGroup", "Title": "", "Logic": 1, "Items": [], "ChildItems": [
            {"Key": "2", "Title": "", "Logic": 1, "Items": [
                {"Key": "F086?", "Title": "Music and Dancing", "Logic": 2, "Name": "专题子栏目代码", "Operate": "",
                 "Value": "F086?", "ExtendType": 14, "ExtendValue": "", "Value2": "", "BlurType": ""}],
             "ChildItems": []}]}]}, "CodeLang": ""}

    return QueryJson


def queryParse(query: str):
    string = unquote(query)
    params = string.split('&')
    formData = {}
    for param in params:
        kvs = param.split('=', maxsplit=1)
        k = kvs[0]
        v = kvs[-1]
        formData[k] = int(v) if v.isdigit() else v
    jsonFM = json.dumps(formData, ensure_ascii=False)
    return formData


# async def retry_func(request):
#     if request.url == 'https://oversea.cnki.net/kns/Brief/GetGridTableHtml':
#
#         time.sleep(3)
#         meta = request.meta
#         headers = request.headers
#         QueryJson = generate_muti_group("CFLQ", meta['sub_name'], meta['year'])
#         data = generate_search_param(QueryJson, "CFLQ", page=1)
#         response = requests.post(url='https://oversea.cnki.net/kns/Brief/GetGridTableHtml', data=data,
#                                     headers=headers)
#         # async with aiohttp.ClientSession() as session:
#         #     async with session.post(url='https://oversea.cnki.net/kns/Brief/GetGridTableHtml', data=data,
#         #                             headers=headers
#         #                             ) as response:
#         res = etree.HTML(response.text)
#         first_hid = res.xpath('//*[@id="HandlerIdHid"]/@value')[0]
#         print(f'第{meta["page"]}更新hid', first_hid)
#         request.data['HandlerId'] = first_hid
#         request.request_config['TIMEOUT'] = 10
#         return request
#     else:
#         return request


class RetryDemo(Spider):
    request_config = {
        "RETRIES": 2,
        "DELAY": 0,
        "TIMEOUT": 10,
        # "RETRY_FUNC": retry_func,
    }
    # 列表页
    url = 'https://oversea.cnki.net/kns/Brief/GetGridTableHtml'
    year_url = 'https://oversea.cnki.net/kns/Group/SingleResult'

    concurrency = 4
    aiohttp_kwargs = {'proxy': 'http://127.0.0.1:1080'}

    headers = {
        "Cookie": "cangjieStatus_OVERSEA2=false; Ecp_ClientId=b221016173201619969; Ecp_ClientIp=121.237.217.55; UM_distinctid=183eaf91a078b6-0c646a46d4ef1e-977173c-144000-183eaf91a08c18; dperpage=50; dsorder=pubdate; ASPSESSIONIDQARDTRTA=LPJKPPEBBEJLHPJBNIGPDOEN; eng_k55_id=123103; Ecp_IpLoginFail=221022121.237.217.55; ASP.NET_SessionId=nouspgfcgudat5b5ytbojb02; knsLeftGroupSelectItem=1%3B2%3B; CurrSortField=Publication+Date%2f(%e5%8f%91%e8%a1%a8%e6%97%b6%e9%97%b4%2c%27TIME%27); CurrSortFieldType=desc; CNZZDATA1279462118=1508356872-1666091275-https%253A%252F%252Foversea.cnki.net%252F%7C1666430456; dblang=ch; _pk_ref=%5B%22%22%2C%22%22%2C1666433370%2C%22https%3A%2F%2Fwww.baidu.com%2Flink%3Furl%3Di8Csp0pHLNmJkJFYN8G10bb-N3B5mxZamgcvGnirAfe%26wd%3D%26eqid%3D945bf58100058a7d00000004634ea68a%22%5D; _pk_id=3fc3a8d4-1b31-416b-86a9-60da97b77b4f.1665912785.4.1666433370.1666433370.; _pk_ses=*",
        "Referer": "https://oversea.cnki.net/kns/AdvSearch?dbcode=CFLS&crossDbcodes=CJFQ,CDMD,CIPD,CCND,CYFD,CCJD,BDZK,CISD,CJFN",
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    }

    async def start_requests(self):
        title_name = "J6 音乐"
        sub_name = title_name.split(' ')[0]

        QueryJson = {"Platform": "", "DBCode": 'CFLQ', "KuaKuCode": "", "QNode": {"QGroup": [
            {"Key": "Subject", "Title": "", "Logic": 4, "Items": [], "ChildItems": [
                {"Key": "input[data-tipid=gradetxt-1]", "Title": "Chinese Library Classification", "Logic": 0,
                 "Items": [
                     {"Key": "", "Title": sub_name, "Logic": 1, "Name": "CLC", "Operate": "=", "Value": sub_name,
                      "ExtendType": 1,
                      "ExtendValue": "中英文对照", "Value2": "", "BlurType": "??"}], "ChildItems": []}]},
            {"Key": "ControlGroup", "Title": "", "Logic": 1, "Items": [], "ChildItems": []}]}, "CodeLang": ""}
        data = {
            "queryJson": json.dumps(QueryJson, ensure_ascii=False),
            "groupId": 3
        }
        meta = dict(title_name=title_name, sub_name=sub_name)
        yield self.request(
            url=self.year_url,
            method='post',
            headers=self.headers,
            data=data,
            meta=meta
        )

    async def parse(self, response):
        meta = response.meta
        res = response.html_etree(html=await response.text())
        years = res.xpath('//div[@class="resultlist"]/ul/li/a/@title')
        print(years)
        for year in years[1:2]:
            sub_name = meta["title_name"].split(' ')[0]
            QueryJson = generate_muti_group("CFLQ", sub_name, year)
            data = generate_search_param(QueryJson, "CFLQ", page=1)
            meta_copy = deepcopy(meta)
            meta_copy['year'] = year
            yield self.request(
                url=self.url,
                method='post',
                headers=self.headers,
                data=data,
                meta=meta_copy,
                callback=self.acticle_list
            )

    async def acticle_list(self, response):
        meta = response.meta
        html = await response.text()
        res = response.html_etree(html=html)
        # 后面都需要用到这个id
        first_hid = res.xpath('//*[@id="HandlerIdHid"]/@value')[0]

        msg = res.xpath('//table[@class="result-table-list"]/tr')
        if '验证码' in html:
            # time.sleep(40)
            meta_copy = deepcopy(meta)
            QueryJson = generate_muti_group("CFLQ", meta['sub_name'], meta['year'])
            data = generate_search_param(QueryJson, "CFLQ", page=meta_copy.get('page', 1))
            yield self.request(
                url=self.url,
                method='post',
                headers=self.headers,
                data=data,
                meta=meta_copy,
                request_config={
                    "RETRIES": 2,
                    "DELAY": 0,
                    "TIMEOUT": 10,
                },
                callback=self.acticle_list
            )
        for one in msg:
            zh_em = []
            article_name = one.xpath('.//td[@class="name"]/a/text()')[0] if one.xpath(
                './/td[@class="name"]/a/text()') else ''
            async with aiofiles.open('./all_art.txt', mode='a', encoding='utf-8') as aof:
                await aof.write(article_name + '\n')
            for str2 in article_name[:10]:
                if u'\u4e00' < str2 < u'\u9fff':
                    zh_em.append('zh')
                else:
                    zh_em.append('em')
            aaa = Counter(zh_em)
            # 如果是英文则下载
            if aaa['zh'] < aaa['em']:
                url_list = one.xpath('.//td[@class="name"]/a/@href')[0] if one.xpath(
                    './/td[@class="name"]/a/@href') else ''
                formData = queryParse(url_list)
                db_code = formData.get('DbCode')
                db_name = formData.get('dbname')
                file_name = formData.get('filename')
                detail_url = f'https://oversea.cnki.net/kcms/detail/detail.aspx?dbcode={db_code}&dbname={db_name}&filename={file_name}'
                yield self.request(
                    url=detail_url,
                    headers=self.headers,
                    meta=deepcopy(meta),
                    callback=self.deal_detail
                )

        # 后面的页
        if meta.get('max_page') is None:
            total_prm = res.xpath('//span[@class="pagerTitleCell"]/em/text()')[0]
            total_prm = total_prm.replace(',', '')
            page_count = math.ceil(int(total_prm) / 50)
            if page_count > 120:
                page_count = 120
            meta['max_page'] = page_count
            self.logger.info(f'当前{meta["title_name"]}的{meta["year"]}的数量为{total_prm}')

            for page in range(2, page_count + 1):
                QueryJson = generate_muti_group("CFLQ", meta['sub_name'], meta['year'])
                data = generate_search_param(QueryJson, "CFLQ", page=page)
                data['HandlerId'] = first_hid
                meta['page'] = page
                meta_copy = deepcopy(meta)
                yield self.request(
                    url=self.url,
                    method='post',
                    headers=self.headers,
                    data=data,
                    meta=meta_copy,
                    callback=self.acticle_list
                )

    async def deal_detail(self, response):
        meta = response.meta
        res = response.html_etree(html=await response.text())
        title_name = res.xpath('//div[@class="wx-tit"]/h1/text()')[0] if res.xpath(
            '//div[@class="wx-tit"]/h1/text()') else ''
        author = res.xpath('//div[@class="wx-tit"]/h3/span/text()')
        author = ''.join(author)
        abstract = res.xpath('//*[@id="ChDivSummary"]//text()')
        abstract = ''.join(abstract)

        keywords = res.xpath('//p[@class="keywords"]/a/text()')  # 关键词
        keywords = [i.replace('\n', '').replace(' ', '') for i in keywords]
        keywords = ''.join(keywords)
        fund = res.xpath('//p[@class="funds"]/a/text()')
        fund = [i.replace('\n', '').replace(' ', '') for i in fund]
        fund = ';'.join(fund)
        doi = res.xpath('//li[@class="top-space"]/span[contains(text(), "DOI：")]/parent::li/p/text()')
        doi = ';'.join(doi)
        series = res.xpath('//li[@class="top-space"]/span[contains(text(), "Series：")]/parent::li/p/text()')
        series = ';'.join(series)
        subject = res.xpath('//li[@class="top-space"]/span[contains(text(), "Subject：")]/parent::li/p/text()')
        subject = ';'.join(subject)
        clc = res.xpath(
            '//li[@class="top-space"]/span[contains(text(), "Classification Code：")]/parent::li/p/text()')
        clc = ';'.join(clc)

        journal_name = res.xpath('//div[@class="top-tip"]/span//text()')
        journal_name = [i.replace('\n', '').replace(' ', '') for i in journal_name]
        journal_name = ';'.join(journal_name)

        data_list = item.CsvItem(data_storage=fr'E:\维普\中图分类号_file\{meta["title_name"]}',
                                 filename=f'{meta["title_name"]}')
        data_list.append(
            dict(title_name=title_name, author=author, abstract=abstract, keywords=keywords, fund=fund, doi=doi,
                 series=series, subject=subject, clc=clc, journal_name=journal_name))
        yield data_list

    # aaa = {
    #     'title_name': 'Mechanism of piR-1245/PIWI-like protein-2 regulating Janus kinase-2/signal transducer and activator of transcription-3/vascular endothelial growth factor signaling pathway in retinal neovascularization',
    #     'author': 'Yong Yu;Li-Kun Xia;Yu Di;Qing-Zhu Nie;Xiao-Long Chen;Department of Ophthalmology, Shengjing Hospital of China Medical University;',
    #     'abstract': 'Inhibiting retinal neovascularization is the optimal strategy for the treatment of retina-related diseases, but there is currently no effective treatment for retinal neovascularization. P-element-induced wimpy testis（PIWI）-interacting RNA（piRNA） is a type of small non-coding RNA implicated in a variety of diseases. In this study, we found that the expression of piR-1245 and the interacting protein PIWIL2 were remarkably increased in human retinal endothelial cells cultured in a hypoxic environment, and cell apoptosis, migration, tube formation and proliferation were remarkably enhanced in these cells. Knocking down piR-1245 inhibited the above phenomena. After intervention by a p-JAK2 activator, piR-1245 decreased the expression of hypoxia inducible factor-1α and vascular endothelial growth factor through the JAK2/STAT3 pathway. For in vivo analysis, 7-day-old newborn mice were raised in 75 ± 2% hyperoxia for 5 days and then piR-1245 in the retina was knocked down. In these mice, the number of newly formed vessels in the retina was decreased, the expressions of inflammationrelated proteins were reduced, the number of apoptotic cells in the retina was decreased, the JAK2/STAT3 pathway was inhibited, and the expressions of hypoxia inducible factor-1α and vascular endothelial growth factor were decreased. Injection of the JAK2 inhibitor JAK2/TYK2-IN-1 into the vitreous cavity inhibited retinal neovascularization in mice and reduced expression of hypoxia inducible factor-1α and vascular endothelial growth factor. These findings suggest that piR-1245 activates the JAK2/STAT3 pathway, regulates the expression of hypoxia inducible factor-1α and vascular endothelial growth factor, and promotes retinal neovascularization. Therefore, piR-1245 may be a new therapeutic target for retinal neovascularization.',
    #     'keywords': 'angiogenesis;\rhumanretinalendothelialcells;\rhypoxiainduciblefactor-1α;\rhypoxia;\rinterleukin-1β;\rmigration;\rnon-codingRNA;\roxygen-inducedinjury;\rPIWI-interactingRNA;\rretinopathy;\r',
    #     'fund': 'supportedbytheNationalNaturalScienceFoundationofChina,No.81570866（toXLC）；\r', 'doi': '',
    #     'series': '(E) Medicine ＆ Public Health', 'subject': 'Ophthalmology and Otolaryngology', 'clc': 'R774.1',
    #     'journal_name': '中国神经再生研究(英文版).\r;2023(05)\r;\rPage:1132-1138'}
    # data_list = item.CsvItem(data_storage='./', filename='test')
    # data_list.append(aaa)
    # yield data_list


if __name__ == "__main__":
    RetryDemo.start(middleware=middleware)
    # 7824
