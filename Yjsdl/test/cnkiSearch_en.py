# -*- coding: utf-8 -*-
import json
import math
import sys
import os
import time
import logging
import pandas as pd
import requests
from lxml import etree
from urllib.parse import unquote
from requests import adapters
# from CNKI.utils.ip import check_ip

sys.path.append(os.getcwd().replace('\\spiders', '').rsplit('\\', maxsplit=1)[0])

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s: %(message)s')


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


# 保存到csv文件
def save_list(data, file, name):
    # desk = os.path.join(os.path.expanduser('~'), 'Desktop')
    # 当前文件夹
    file_path = os.path.dirname(__file__) + '/' + file
    if os.path.isfile(file_path):
        df = pd.DataFrame(data=data)
        df.to_csv(file_path, encoding="utf-8", mode='a', header=False, index=False)
    else:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        df = pd.DataFrame(data=data, columns=name)
        df.to_csv(file_path, encoding="utf-8", index=False)


# 第一次请求获取hid
def renew_hid(name, sub_name, year):
    url = 'https://oversea.cnki.net/kns/Brief/GetGridTableHtml'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        'Referer': 'https://oversea.cnki.net/kns/AdvSearch?dbcode=CFLS&crossDbcodes=CJFQ,CDMD,CIPD,CCND,CYFD,CCJD,BDZK,CISD,CJFN',
        'Cookie': 'cangjieStatus_OVERSEA2=false; Ecp_ClientId=3220420165906692312; Ecp_ClientIp=58.212.197.233; cnkiUserKey=ee6aa094-fcc6-a640-b23b-10ad197d8a3b; UM_distinctid=1805942f889139-08460b80622352-6b3e555b-1fa400-1805942f88a19c; Ecp_loginuserbk=SJTU; ASPSESSIONIDQAQARSQB=IGLLNFLDHBJLFBNFBJCDKCHH; eng_k55_id=123103; ASP.NET_SessionId=ilohuot5qitecjljviujyzir; knsLeftGroupSelectItem=1%3B2%3B; CurrSortFieldType=desc; _pk_ref=%5B%22%22%2C%22%22%2C1663571791%2C%22https%3A%2F%2Fwww.baidu.com%2Flink%3Furl%3DqAyApXZe7PsZK9kKQnBIEEf99Su4R9AoFfYWu3EyTO7%26wd%3D%26eqid%3Daac36a410010483b000000046328174c%22%5D; _pk_id=1da07332-73dd-494e-b5d9-3a9b652545aa.1650445190.30.1663571791.1663571791.; ASPSESSIONIDQCSDQQTA=JACKACDCAOAFCOMKELGEGIIF; dstyle=listmode; dsorder=pubdate; CurrSortField=Publication+Date%2f(%e5%8f%91%e8%a1%a8%e6%97%b6%e9%97%b4%2c%27TIME%27); ASPSESSIONIDQCQBRTSB=KFFFOMIAANJBPBIJBDIDDCCM; Ecp_IpLoginFail=22101758.212.197.250; ASPSESSIONIDSCQDTQTA=GIKMHACCABAJAAIOCEMOEMHK; CNZZDATA1279462118=620665052-1650760587-%7C1665995467; dblang=ch; dperpage=50; searchTimeFlag=1',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    }
    # 获取请求参数，
    en_nameid = literature_category.get(name)
    QueryJson = generate_muti_group(en_nameid, sub_name, year)
    data = generate_search_param(QueryJson, en_nameid, page=1)
    # 第一次请求拿到hid， 后面需要
    res = requests.post(url, headers=headers, data=data)
    if '抱歉，暂无数据，可尝试更换检索词。' in res.text:
        return '', '', ''
    response = etree.HTML(res.text)
    # 文献的标识符，导出的时候需要用到

    msg = response.xpath('//table[@class="result-table-list"]/tr')
    msg_lists = []
    for one in msg:
        onelist = []
        url_list = one.xpath('.//td[@class="name"]/a/@href')[0] if one.xpath('.//td[@class="name"]/a/@href') else ''
        is_english = one.xpath('.//td/span[@title="Chinese Full Text"]/text()')[0] if one.xpath('.//td/span[@title="Chinese Full Text"]/text()') else ''
        onelist.append(url_list)
        onelist.append(is_english)
        msg_lists.append(onelist)

    first_hid = response.xpath('//*[@id="HandlerIdHid"]/@value')[0]
    # 当前文献的数量
    total_prm = response.xpath('//span[@class="pagerTitleCell"]/em/text()')[0]
    total_prm = total_prm.replace(',', '')

    return first_hid, msg_lists, total_prm


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


# 获取时间年份
def get_time(en_id, name):
    url = 'https://oversea.cnki.net/kns/Group/SingleResult'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        'Referer': 'https://oversea.cnki.net/kns/AdvSearch?dbcode=CFLS&crossDbcodes=CJFQ,CDMD,CIPD,CCND,CYFD,CCJD,BDZK,CISD,CJFN',
        'Cookie': 'cangjieStatus_OVERSEA2=false; Ecp_ClientId=3220420165906692312; Ecp_ClientIp=58.212.197.233; cnkiUserKey=ee6aa094-fcc6-a640-b23b-10ad197d8a3b; UM_distinctid=1805942f889139-08460b80622352-6b3e555b-1fa400-1805942f88a19c; Ecp_loginuserbk=SJTU; ASPSESSIONIDQAQARSQB=IGLLNFLDHBJLFBNFBJCDKCHH; eng_k55_id=123103; ASP.NET_SessionId=ilohuot5qitecjljviujyzir; CurrSortFieldType=desc; _pk_ref=%5B%22%22%2C%22%22%2C1663571791%2C%22https%3A%2F%2Fwww.baidu.com%2Flink%3Furl%3DqAyApXZe7PsZK9kKQnBIEEf99Su4R9AoFfYWu3EyTO7%26wd%3D%26eqid%3Daac36a410010483b000000046328174c%22%5D; _pk_id=1da07332-73dd-494e-b5d9-3a9b652545aa.1650445190.30.1663571791.1663571791.; ASPSESSIONIDQCSDQQTA=JACKACDCAOAFCOMKELGEGIIF; dstyle=listmode; dsorder=pubdate; CurrSortField=Publication+Date%2f(%e5%8f%91%e8%a1%a8%e6%97%b6%e9%97%b4%2c%27TIME%27); ASPSESSIONIDQCQBRTSB=KFFFOMIAANJBPBIJBDIDDCCM; Ecp_IpLoginFail=22101758.212.197.250; ASPSESSIONIDSCQDTQTA=GIKMHACCABAJAAIOCEMOEMHK; CNZZDATA1279462118=620665052-1650760587-%7C1665995467; dblang=ch; dperpage=50; searchTimeFlag=1; knsLeftGroupSelectItem=1%3B2%3B3%3B',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    }

    QueryJson = {"Platform": "", "DBCode": en_id, "KuaKuCode": "", "QNode": {"QGroup": [
        {"Key": "Subject", "Title": "", "Logic": 4, "Items": [], "ChildItems": [
            {"Key": "input[data-tipid=gradetxt-1]", "Title": "Chinese Library Classification", "Logic": 0, "Items": [
                {"Key": "", "Title": name, "Logic": 1, "Name": "CLC", "Operate": "=", "Value": name, "ExtendType": 1,
                 "ExtendValue": "中英文对照", "Value2": "", "BlurType": "??"}], "ChildItems": []}]},
        {"Key": "ControlGroup", "Title": "", "Logic": 1, "Items": [], "ChildItems": []}]}, "CodeLang": ""}

    data = {
        "queryJson": json.dumps(QueryJson, ensure_ascii=False),
        "groupId": 3
    }
    res = requests.post(url, headers=headers, data=data).text
    response = etree.HTML(res)
    years = response.xpath('//div[@class="resultlist"]/ul/li/a/@title')
    print(years)
    return years


# 获取每个类别下的文献
def get_content(name, sub_name, title_name, file_num):
    en_nameid = literature_category.get(name)
    years = get_time(en_nameid, sub_name)
    for year in years[1:2]:

        # 下载数量
        logging.info(f'当前{title_name}下载数量为{file_num}')
        if file_num > 13000:
            break

        logging.info(f'当前是 {sub_name} 的 {year} 年')
        url = 'https://oversea.cnki.net/kns/Brief/GetGridTableHtml'

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
            'Referer': 'https://oversea.cnki.net/kns/AdvSearch?dbcode=CFLS&crossDbcodes=CJFQ,CDMD,CIPD,CCND,CYFD,CCJD,BDZK,CISD,CJFN',
            'Cookie': 'cangjieStatus_OVERSEA2=false; Ecp_ClientId=3220420165906692312; Ecp_ClientIp=58.212.197.233; cnkiUserKey=ee6aa094-fcc6-a640-b23b-10ad197d8a3b; UM_distinctid=1805942f889139-08460b80622352-6b3e555b-1fa400-1805942f88a19c; Ecp_loginuserbk=SJTU; ASPSESSIONIDQAQARSQB=IGLLNFLDHBJLFBNFBJCDKCHH; eng_k55_id=123103; ASP.NET_SessionId=ilohuot5qitecjljviujyzir; knsLeftGroupSelectItem=1%3B2%3B; CurrSortFieldType=desc; _pk_ref=%5B%22%22%2C%22%22%2C1663571791%2C%22https%3A%2F%2Fwww.baidu.com%2Flink%3Furl%3DqAyApXZe7PsZK9kKQnBIEEf99Su4R9AoFfYWu3EyTO7%26wd%3D%26eqid%3Daac36a410010483b000000046328174c%22%5D; _pk_id=1da07332-73dd-494e-b5d9-3a9b652545aa.1650445190.30.1663571791.1663571791.; ASPSESSIONIDQCSDQQTA=JACKACDCAOAFCOMKELGEGIIF; dstyle=listmode; dsorder=pubdate; CurrSortField=Publication+Date%2f(%e5%8f%91%e8%a1%a8%e6%97%b6%e9%97%b4%2c%27TIME%27); ASPSESSIONIDQCQBRTSB=KFFFOMIAANJBPBIJBDIDDCCM; Ecp_IpLoginFail=22101758.212.197.250; ASPSESSIONIDSCQDTQTA=GIKMHACCABAJAAIOCEMOEMHK; CNZZDATA1279462118=620665052-1650760587-%7C1665995467; dblang=ch; dperpage=50; searchTimeFlag=1',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        }

        first_hid, filenames, total_prm = renew_hid(name, sub_name, year)
        if filenames == '':
            logging.info(f'{sub_name}没有期刊发文')
            with open('./download.txt', 'a', encoding='utf-8') as f:
                f.write(f'{sub_name}的{year}没有期刊发文' + '\n')
            continue

        # first page
        # for one_file in filenames:
        #     link = one_file[0]
        #     isEN = one_file[1]
        #     if isEN:
        #         formData = queryParse(link)
        #         file_num += 1
        #         try:
        #             time.sleep(0.5)
        #             logging.info(f'当前{title_name}下载数量为{file_num}')
        #             print(link)
        #             detail_parse(formData, title_name)
        #         except:
        #             raise ValueError(f'{sub_name}的{year}年第1页出错')

        page_count = math.ceil(int(total_prm) / 50)
        print(f'{sub_name}的{year}数量为{int(total_prm)} 页数为 %d' % page_count)

        if page_count > 120:
            page_count = 120

        # 从第二个页面开始请求
        for page in range(70, page_count + 1):
            if file_num > 13000:
                break
            try:
                # 获取请求参数

                QueryJson = generate_muti_group(en_nameid, sub_name, year)
                data = generate_search_param(QueryJson, en_nameid, page=page)
                time.sleep(1)
                # 更新hid
                if page in [30, 60, 70, 80, 90, 100, 110, 120]:
                    first_hid, str1, str2 = renew_hid(name, sub_name, year)

                data['HandlerId'] = first_hid
                res = requests.post(url, headers=headers, data=data).text

                response = etree.HTML(res)

                msg = response.xpath('//table[@class="result-table-list"]/tr')
                msg_lists = []
                for one in msg:
                    onelist = []
                    url_list = one.xpath('.//td[@class="name"]/a/@href')[0] if one.xpath(
                        './/td[@class="name"]/a/@href') else ''
                    is_english = one.xpath('.//td/span[@title="Chinese Full Text"]/text()')[0] if one.xpath(
                        './/td/span[@title="Chinese Full Text"]/text()') else ''
                    onelist.append(url_list)
                    onelist.append(is_english)
                    msg_lists.append(onelist)

                for one_file in filenames:
                    link = one_file[0]
                    isEN = one_file[1]
                    if isEN:

                        formData = queryParse(link)
                        file_num += 1
                        try:
                            time.sleep(0.5)
                            logging.info(f'当前{title_name}的{year}第{page}页下载数量为{file_num}')
                            detail_parse(formData, title_name)
                        except:
                            raise ValueError(f'{sub_name}')
            except Exception as e:
                raise ValueError(f'{sub_name}的{year}年第{page}页出错')


def detail_parse(formData, titlename):
    data = []
    db_code = formData.get('DbCode')
    db_name = formData.get('dbname')
    file_name = formData.get('filename')
    url = f'https://oversea.cnki.net/kcms/detail/detail.aspx?dbcode={db_code}&dbname={db_name}&filename={file_name}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        'Cookie': 'cangjieStatus_OVERSEA2=false; Ecp_ClientId=3220420165906692312; Ecp_ClientIp=58.212.197.233; cnkiUserKey=ee6aa094-fcc6-a640-b23b-10ad197d8a3b; UM_distinctid=1805942f889139-08460b80622352-6b3e555b-1fa400-1805942f88a19c; Ecp_loginuserbk=SJTU; ASPSESSIONIDQAQARSQB=IGLLNFLDHBJLFBNFBJCDKCHH; eng_k55_id=123103; ASP.NET_SessionId=ilohuot5qitecjljviujyzir; knsLeftGroupSelectItem=1%3B2%3B; CurrSortFieldType=desc; _pk_ref=%5B%22%22%2C%22%22%2C1663571791%2C%22https%3A%2F%2Fwww.baidu.com%2Flink%3Furl%3DqAyApXZe7PsZK9kKQnBIEEf99Su4R9AoFfYWu3EyTO7%26wd%3D%26eqid%3Daac36a410010483b000000046328174c%22%5D; _pk_id=1da07332-73dd-494e-b5d9-3a9b652545aa.1650445190.30.1663571791.1663571791.; ASPSESSIONIDQCSDQQTA=JACKACDCAOAFCOMKELGEGIIF; dstyle=listmode; dsorder=pubdate; CurrSortField=Publication+Date%2f(%e5%8f%91%e8%a1%a8%e6%97%b6%e9%97%b4%2c%27TIME%27); ASPSESSIONIDQCQBRTSB=KFFFOMIAANJBPBIJBDIDDCCM; Ecp_IpLoginFail=22101758.212.197.250; ASPSESSIONIDSCQDTQTA=GIKMHACCABAJAAIOCEMOEMHK; CNZZDATA1279462118=620665052-1650760587-%7C1665995467; dblang=ch; dperpage=50; searchTimeFlag=1',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    }
    response = requests.get(url=url, headers=headers).text
    res = etree.HTML(response)
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
    clc = res.xpath('//li[@class="top-space"]/span[contains(text(), "Classification Code：")]/parent::li/p/text()')
    clc = ';'.join(clc)

    journal_name = res.xpath('//div[@class="top-tip"]/span//text()')
    journal_name = [i.replace('\n', '').replace(' ', '') for i in journal_name]
    journal_name = ';'.join(journal_name)
    data.append(dict(title_name=title_name, author=author, abstract=abstract, keywords=keywords, fund=fund, doi=doi,
                series=series, subject=subject, clc=clc, journal_name=journal_name))
    name = ['title_name', 'author', 'abstract', 'keywords', 'fund', 'doi', 'series', 'subject', 'clc', 'journal_name']
    save_list(data, f'file_em/file_in/{titlename}/1.csv', name)


if __name__ == '__main__':
    # 文献类别，# CFLQ 学术期刊 CDMD 论文 CFLP 会议 CCND 报纸 SNAD 成果 WBFD 中文图书
    literature_category = {
        "学术期刊": 'CFLQ',
        '论文': 'CDMD',
        '会议': 'CFLP',
        '报纸': 'CCND',
        '成果': 'SNAD',
        '中文图书': 'WBFD',
    }
    pf = pd.read_csv('英文下载.csv', dtype=str).fillna('')
    sha = pf.shape[0]
    sunm = 49
    for i in range(sunm, sunm + 1):
        clc = pf.values[i][0]
        # clc = "P75 海洋工程"
        if clc:
            # 分割每一个分类号
            clc_ens = clc.split('；')
            for title_name in clc_ens:
                file_num = 2508
                sub_name = title_name.split(' ')[0]
                if sub_name:
                    if os.path.exists(fr'F:\CNKI主站\中图分类号\file_em\file_in\{title_name}'):
                        print(f'{title_name}已经存在')
                    # print(sub_name)
                    logging.info('当前为第%d - 学科为 %s' % (i, sub_name))
                    get_content('学术期刊', sub_name, title_name, file_num)
