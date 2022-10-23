# -*- coding: utf-8 -*-
# @Time    : 2022/10/23 2:35
# @Author  : Liuyijie
# @File    : hidmiddleware.py
from Yjsdl.middleware import Middleware
from lxml import etree
import aiohttp
import json

middleware = Middleware()


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
    QueryJson = {"Platform": "", "DBCode": en_id, "KuaKuCode": "", "QNode": {"QGroup": [
        {"Key": "Subject", "Title": "", "Logic": 4, "Items": [], "ChildItems": [
            {"Key": "input[data-tipid=gradetxt-1]", "Title": "Chinese Library Classification", "Logic": 0, "Items": [
                {"Key": "", "Title": sub_name, "Logic": 1, "Name": "CLC", "Operate": "=", "Value": sub_name,
                 "ExtendType": 1,
                 "ExtendValue": "中英文对照", "Value2": "", "BlurType": "??"}], "ChildItems": []}]},
        {"Key": "ControlGroup", "Title": "", "Logic": 1, "Items": [], "ChildItems": []},
        {"Key": "MutiGroup", "Title": "", "Logic": 1, "Items": [], "ChildItems": [{"Key": "3", "Title": "", "Logic": 1,
                                                                                   "Items": [
                                                                                       {"Key": year, "Title": year,
                                                                                        "Logic": 2, "Name": "年",
                                                                                        "Operate": "", "Value": year,
                                                                                        "ExtendType": 0,
                                                                                        "ExtendValue": "", "Value2": "",
                                                                                        "BlurType": ""}],
                                                                                   "ChildItems": []}]}]},
                 "CodeLang": ""}

    # QueryJson = {"Platform": "", "DBCode": en_id, "KuaKuCode": "", "QNode": {"QGroup": [
    #     {"Key": "Subject", "Title": "", "Logic": 4, "Items": [], "ChildItems": [
    #         {"Key": "input[data-tipid=gradetxt-1]", "Title": "中图分类号", "Logic": 0, "Items": [
    #             {"Key": "", "Title": sub_name, "Logic": 1, "Name": "CLC", "Operate": "=", "Value": sub_name,
    #              "ExtendType": 1,
    #              "ExtendValue": "中英文对照", "Value2": "", "BlurType": "??"}], "ChildItems": []}]},
    #     {"Key": "ControlGroup", "Title": "", "Logic": 1, "Items": [], "ChildItems": [
    #         {"Key": ".tit-startend-yearbox", "Title": "", "Logic": 1, "Items": [
    #             {"Key": ".tit-startend-yearbox", "Title": "出版年度", "Logic": 1, "Name": "YE", "Operate": "",
    #              "Value": year, "ExtendType": 2, "ExtendValue": "", "Value2": year, "BlurType": ""}],
    #          "ChildItems": []}]},
    #     {"Key": "ControlGroup", "Title": "", "Logic": 1, "Items": [], "ChildItems": []},
    #     {"Key": "MutiGroup", "Title": "", "Logic": 1, "Items": [], "ChildItems": [{"Key": "2", "Title": "", "Logic": 1,
    #                                                                                "Items": [
    #                                                                                    {"Key": "A010?", "Title": "海洋学",
    #                                                                                     "Logic": 2, "Name": "专题子栏目代码",
    #                                                                                     "Operate": "", "Value": "A010?",
    #                                                                                     "ExtendType": 14,
    #                                                                                     "ExtendValue": "", "Value2": "",
    #                                                                                     "BlurType": ""}],
    #                                                                                "ChildItems": []}]}]}}

    return QueryJson


@middleware.request
async def get_FirstHid(spider_ins, request):
    meta = request.meta
    if request.url == 'https://oversea.cnki.net/kns/Brief/GetGridTableHtml' and meta.get('page'):

        headers = request.headers
        QueryJson = generate_muti_group("CFLQ", meta['sub_name'], meta['year'])
        data = generate_search_param(QueryJson, "CFLQ", page=1)
        # response = requests.post(url='https://oversea.cnki.net/kns/Brief/GetGridTableHtml', data=data,
        #                             headers=headers)
        async with aiohttp.ClientSession() as session:
            async with session.post(url='https://oversea.cnki.net/kns/Brief/GetGridTableHtml', data=data,
                                    headers=headers
                                    ) as response:
                res = etree.HTML(await response.text())
                first_hid = res.xpath('//*[@id="HandlerIdHid"]/@value')[0]
                print(f'第{meta["page"]}更新hid', first_hid)
                request.data['HandlerId'] = first_hid
                request.request_config['TIMEOUT'] = 10
                return request
    else:
        return request