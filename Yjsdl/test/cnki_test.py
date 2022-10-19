# -*- coding: utf-8 -*-
# @Time    : 2022/10/16 16:48
# @Author  : Liuyijie
# @File    : cnki_test.py
import math

from Yjsdl import Spider, Request
from middlewares import middleware
import json
import aiofiles
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
    QueryJson = {"Platform": "", "DBCode": en_id, "KuaKuCode": "", "QNode": {"QGroup": [
        {"Key": "Subject", "Title": "", "Logic": 4, "Items": [], "ChildItems": [
            {"Key": "input[data-tipid=gradetxt-1]", "Title": "中图分类号", "Logic": 0, "Items": [
                {"Key": "", "Title": sub_name, "Logic": 1, "Name": "CLC", "Operate": "=", "Value": sub_name,
                 "ExtendType": 1,
                 "ExtendValue": "中英文对照", "Value2": "", "BlurType": "??"}], "ChildItems": []}]},
        {"Key": "ControlGroup", "Title": "", "Logic": 1, "Items": [], "ChildItems": [
            {"Key": ".tit-startend-yearbox", "Title": "", "Logic": 1, "Items": [
                {"Key": ".tit-startend-yearbox", "Title": "出版年度", "Logic": 1, "Name": "YE", "Operate": "",
                 "Value": year, "ExtendType": 2, "ExtendValue": "", "Value2": year, "BlurType": ""}],
             "ChildItems": []}]}]}}

    return QueryJson


async def again_gethid(request):
    pass


class CnkiTest(Spider):
    request_config = {
        "RETRIES": 3,
        "DELAY": 2,
        "RETRY_DELAY": 0,
        "TIMEOUT": 100,
        # 设置重试的参数
        # "RETRY_FUNC": Coroutine,
    }
    concurrency = 3

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        'Referer': 'https://oversea.cnki.net/kns/AdvSearch?dbcode=CFLS&crossDbcodes=CJFQ,CDMD,CIPD,CCND,CYFD,CCJD,BDZK,CISD,CJFN',
        'Cookie': 'cangjieStatus_OVERSEA2=false; Ecp_ClientId=3220420165906692312; Ecp_ClientIp=58.212.197.233; cnkiUserKey=ee6aa094-fcc6-a640-b23b-10ad197d8a3b; UM_distinctid=1805942f889139-08460b80622352-6b3e555b-1fa400-1805942f88a19c; Ecp_loginuserbk=SJTU; ASPSESSIONIDQAQARSQB=IGLLNFLDHBJLFBNFBJCDKCHH; eng_k55_id=123103; ASP.NET_SessionId=ilohuot5qitecjljviujyzir; knsLeftGroupSelectItem=1%3B2%3B; CurrSortFieldType=desc; _pk_ref=%5B%22%22%2C%22%22%2C1663571791%2C%22https%3A%2F%2Fwww.baidu.com%2Flink%3Furl%3DqAyApXZe7PsZK9kKQnBIEEf99Su4R9AoFfYWu3EyTO7%26wd%3D%26eqid%3Daac36a410010483b000000046328174c%22%5D; _pk_id=1da07332-73dd-494e-b5d9-3a9b652545aa.1650445190.30.1663571791.1663571791.; ASPSESSIONIDQCSDQQTA=JACKACDCAOAFCOMKELGEGIIF; dstyle=listmode; dsorder=pubdate; CurrSortField=Publication+Date%2f(%e5%8f%91%e8%a1%a8%e6%97%b6%e9%97%b4%2c%27TIME%27); ASPSESSIONIDQCQBRTSB=KFFFOMIAANJBPBIJBDIDDCCM; Ecp_IpLoginFail=22101758.212.197.250; ASPSESSIONIDSCQDTQTA=GIKMHACCABAJAAIOCEMOEMHK; CNZZDATA1279462118=620665052-1650760587-%7C1665995467; dblang=ch; dperpage=50; searchTimeFlag=1',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    }

    async def start_requests(self):
        for year in range(2019, 2020):
            QueryJson = generate_muti_group("CFLQ", "A8", year)
            data = generate_search_param(QueryJson, "CFLQ", page=1)
            meta = dict(year=year, name="A8", filename='1-50')
            yield self.request(
                url='https://oversea.cnki.net/kns/Brief/GetGridTableHtml',
                headers=self.headers,
                method='post',
                data=data,
                meta=meta,
                callback=self.parse
            )

    async def parse(self, response):
        # print(await response.text())
        meta = response.meta
        res = response.html_etree(html=await response.text())
        # 每个文件名
        filenames = res.xpath('//input[@name="CookieName"]/@value')
        # hid
        first_hid = response.xpath('//*[@id="HandlerIdHid"]/@value')[0]
        # 当前文献的数量
        total_prm = res.xpath('//span[@class="pagerTitleCell"]/em/text()')[0]
        total_prm = total_prm.replace(',', '')
        # print(filenames)
        self.logger.info('%s, %s年数量为%s' % (meta['name'], meta['year'], total_prm))

        filenames = ','.join(filenames)

        data = {
            'filename': filenames,
            'displaymode': 'selfDefine',
            'orderparam': 0,
            'ordertype': 'desc',
            'selectfield': 'SrcDatabase-来源库,Title-题名,Author-作者,Organ-单位,Source-文献来源,Keyword-关键词,Summary-摘要,PubTime-发表时间,FirstDuty-第一责任人,Fund-基金,Year-年,Volume-卷,Period-期,PageCount-页码,CLC-中图分类号,ISSN-国际标准刊号,URL-网址,DOI-DOI,',
            'Type': 'xls',
        }
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Refere': 'https://kns.cnki.net/kns8/manage/export.html?displaymode=selfDefine',
            'Cookie': 'cangjieConfig_NZKPT2=%7B%22status%22%3Atrue%2C%22startTime%22%3A%222021-12-23%22%2C%22endTime%22%3A%222022-05-26%22%2C%22orginHosts%22%3A%22kns.cnki.net%22%2C%22type%22%3A%22mix%22%2C%22poolSize%22%3A%2210%22%2C%22intervalTime%22%3A10000%2C%22persist%22%3Afalse%7D; Ecp_ClientId=3220420165906692312; Ecp_ClientIp=58.212.197.233; cnkiUserKey=ee6aa094-fcc6-a640-b23b-10ad197d8a3b; knsLeftGroupSelectItem=1%3B2%3B; UM_distinctid=1805942f889139-08460b80622352-6b3e555b-1fa400-1805942f88a19c; Login_UserAMID=wap_261a28be-2ecc-4610-bda0-e041ee914da7; SID_sug=126003; Ecp_session=1; Ecp_loginuserbk=SJTU; ASP.NET_SessionId=bkzghibydfe0zfalm52vvtik; SID_kns8=015123156; dblang=ch; SID_kns_new=kns123104; SID_recommendapi=126003; CurrSortFieldType=desc; SID_docpre=006007; SID_kcms=025126026; yeswholedownload=%3Bjdzg201404022; dperpage=50; Ecp_IpLoginFail=220513117.89.12.228; dsorder=pubdate; CurrSortField=%e5%8f%91%e8%a1%a8%e6%97%b6%e9%97%b4%2f(%e5%8f%91%e8%a1%a8%e6%97%b6%e9%97%b4%2c%27time%27); _pk_ref=%5B%22%22%2C%22%22%2C1652424776%2C%22https%3A%2F%2Fwww.cnki.net%2F%22%5D; _pk_ses=*; _pk_id=1da07332-73dd-494e-b5d9-3a9b652545aa.1650445190.17.1652425847.1652421133.; CurrSortField=%e5%8f%91%e8%a1%a8%e6%97%b6%e9%97%b4%2f(%e5%8f%91%e8%a1%a8%e6%97%b6%e9%97%b4%2c%27time%27); CurrSortFieldType=desc',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://kns.cnki.net',
        }
        meta_copy = deepcopy(meta)
        yield self.request(
            url='https://kns.cnki.net/kns8/manage/FileToText',
            method="post",
            data=data,
            headers=headers,
            meta=meta_copy,
            callback=self.save_file
        )
        if not meta.get('max_page', ''):
            meta['max_page'] = math.ceil(int(total_prm) / 50)
            if meta['max_page'] > 120:
                meta['max_page'] = 120
            for page in range(2, 3):
                file = str((page - 1) * 50) + '-' + str(page * 50)
                meta['filename'] = file
                meta_copy = deepcopy(meta)

                QueryJson = generate_muti_group("CFLQ", "A8", meta['year'])
                data = generate_search_param(QueryJson, "CFLQ", page=page)
                data['HandlerId'] = first_hid
                yield self.request(
                    url='https://kns.cnki.net/kns8/Brief/GetGridTableHtml',
                    headers=self.headers,
                    method='post',
                    data=data,
                    meta=meta_copy,
                )

    async def save_file(self, response):
        meta = response.meta
        print('save_file', meta)
        res = await response.read()
        async with aiofiles.open(f'{meta["filename"]}.xls', mode='wb') as f:
            await f.write(res)


if __name__ == '__main__':
    CnkiTest.start(middleware=middleware)
