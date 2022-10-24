# -*- coding: utf-8 -*-
# @Time    : 2022/10/10 22:11
# @Author  : 10749
# @File    : test_spider.py

from Yjsdl import Request, Response, Spider


async def valid(response):
    response.headers = {
        'User-Agent': '123456'
    }
    return response


class TestSpider(Spider):
    request_config = {
        "RETRIES": 1,
        "DELAY": 0,
        "TIMEOUT": 20,
        "VALID": valid
    }
    # 并发
    concurrency = 2
    # aiohttp_kwargs = {'proxy': 'https://127.0.0.1:1080'}

    start_urls = ['https://www.baidu.com']

    async def parse(self, response):
        html = await response.text()
        print(response.status)
        print(html)
        # print(response.headers)


if __name__ == '__main__':
    TestSpider.start()
