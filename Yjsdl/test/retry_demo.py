#!/usr/bin/env python

from Yjsdl import Spider
from Yjsdl import Request


async def retry_func(request):
    request.request_config["TIMEOUT"] = 10


class RetryDemo(Spider):
    request_config = {
        "RETRIES": 3,
        "DELAY": 0,
        "TIMEOUT": 2,
        "RETRY_FUNC": retry_func,
    }

    #
    # start_urls = ["http://httpbin.org/get"]

    async def start_requests(self):
        yield self.request(
            url="http://httpbin.org/get"
        )

    async def parse(self, response):

        html = await response.text()

        # for url in ["http://httpbin.org/get?p=1", "http://httpbin.org/get?p=2"]:
        #     yield Request(url, callback=self.parse_item)

        # print(await response.json())
        # print(response.headers)
        # pages = ["http://httpbin.org/get?p=1", "http://httpbin.org/get?p=2"]
        # async for resp in self.multiple_request(pages):
        #     yield self.parse_item(response=resp)

    async def parse_item(self, response):
        json_data = await response.json()
        print(json_data)


if __name__ == "__main__":
    RetryDemo.start(middleware=middleware)
