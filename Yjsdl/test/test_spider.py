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
        "RETRIES": 3,
        "DELAY": 0,
        "TIMEOUT": 20,
        "VALID": valid
    }
    # 并发
    concurrency = 2

    start_requests = {
        "urls": ["http://httpbin.org/get"],
        "mothod": "GET",
    }

    async def parse(self, response):
        html = await response.text()
        print(html)
        print(response.headers)


if __name__ == '__main__':
    TestSpider.start()
