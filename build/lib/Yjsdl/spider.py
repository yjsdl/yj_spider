#!/usr/bin/env python

import asyncio
import collections
import sys
import typing
import weakref

from datetime import datetime
from functools import reduce
from inspect import isawaitable
from signal import SIGINT, SIGTERM
from types import AsyncGeneratorType

from aiohttp import ClientSession

from Yjsdl.exceptions import (
    InvalidCallbackResult,
    NothingMatchedError,
    NotImplementedParseError,
    SpiderHookError,
)
from Yjsdl.item import Item
from Yjsdl.middleware import Middleware
from Yjsdl.request import Request
from Yjsdl.response import Response
from Yjsdl.utils import get_logger

if (
        sys.version_info[0] == 3
        and sys.version_info[1] >= 8
        and sys.platform.startswith("win")
):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if sys.version_info >= (3, 9):
    async_all_tasks = asyncio.all_tasks
    async_current_task = asyncio.current_task
else:
    async_all_tasks = asyncio.Task.all_tasks
    async_current_task = asyncio.tasks.Task.current_task
try:
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass


class SpiderHook:
    """
    SpiderHook is used for extend spider
    """

    callback_result_map: dict = None

    async def _run_spider_hook(self, hook_func):
        """
        Run hook before/after spider start crawling
        :param hook_func: aws function
        :return:
        """
        if callable(hook_func):
            try:
                aws_hook_func = hook_func(weakref.proxy(self))
                if isawaitable(aws_hook_func):
                    await aws_hook_func
            except Exception as e:
                raise SpiderHookError(f"<Hook {hook_func.__name__}: {e}")

    async def process_failed_response(self, request, response):
        """
        Corresponding processing for the failed response
        :param request: Request
        :param response: Response
        :return:
        """
        pass

    async def process_succeed_response(self, request, response):
        """
        Corresponding processing for the succeed response
        :param request: Request
        :param response: Response
        :return:
        """
        pass

    async def process_item(self, item):
        """
        Corresponding processing for the Item type
        :param item: Item
        :return:
        """
        pass

    async def process_callback_result(self, callback_result):
        """
        Corresponding processing for the invalid callback result
        :param callback_result: Custom instance
        :return:
        """
        callback_result_name = type(callback_result).__name__
        process_func_name = self.callback_result_map.get(callback_result_name, "")
        process_func = getattr(self, process_func_name, None)
        if process_func is not None:
            await process_func(callback_result)
        else:
            raise InvalidCallbackResult(
                f"<Parse invalid callback result type: {callback_result_name}>"
            )


class Spider(SpiderHook):
    """
    Spider is used for control requests better
    """

    name = "Yjsdl"
    # 请求配置
    request_config = None

    start_urls: list = []
    # Default values passing to each request object. Not implemented yet.

    # meta: dict = None
    aiohttp_kwargs: dict = None

    # Some fields for statistics
    failed_counts: int = 0
    success_counts: int = 0

    # Concurrency control
    worker_numbers: int = 3
    # 并发
    concurrency: int = 3

    # A queue to save coroutines
    worker_tasks: list = []

    def __init__(
            self,
            middleware: typing.Union[typing.Iterable, Middleware] = None,
            loop=None,
            is_async_start: bool = False,
            cancel_tasks: bool = True,
            **spider_kwargs,
    ):
        """
        Init spider object.
        :param middleware: a list of or a single Middleware
        :param loop: asyncio event llo
        :param is_async_start: start spider by using async
        :param spider_kwargs
        """

        if not self.start_urls and not isinstance(self.start_requests(), AsyncGeneratorType):
            raise ValueError(
                "Your subject should have start_urls or async function example: start_urls = ['www.baidu.com'] ")

        self.loop = loop
        asyncio.set_event_loop(self.loop)

        # Init object-level properties
        self.callback_result_map = self.callback_result_map or {}

        self.request_config = self.request_config or {}

        self.aiohttp_kwargs = self.aiohttp_kwargs or {}
        self.spider_kwargs = spider_kwargs
        self.request_config = self.request_config or {}
        self.request_session = ClientSession()

        self.cancel_tasks = cancel_tasks
        self.is_async_start = is_async_start

        # set logger
        self.logger = get_logger(name=self.name)

        # customize middleware
        if isinstance(middleware, list):
            self.middleware = reduce(lambda x, y: x + y, middleware)
        else:
            self.middleware = middleware or Middleware()

        # async queue as a producer
        self.request_queue = asyncio.Queue()

        # semaphore, used for concurrency control
        self.sem = asyncio.Semaphore(self.concurrency)

    async def _process_async_callback(
            self, callback_results: AsyncGeneratorType, response: Response = None
    ):
        try:
            async for callback_result in callback_results:
                if isinstance(callback_result, AsyncGeneratorType):
                    await self._process_async_callback(callback_result)
                elif isinstance(callback_result, Request):
                    self.request_queue.put_nowait(
                        self.handle_request(request=callback_result)
                    )
                elif isinstance(callback_result, typing.Coroutine):
                    self.request_queue.put_nowait(
                        self.handle_callback(
                            aws_callback=callback_result, response=response
                        )
                    )
                elif isinstance(callback_result, Item):
                    # Process target item
                    await self.process_item(callback_result)
                else:
                    await self.process_callback_result(callback_result=callback_result)
        except NothingMatchedError as e:
            error_info = f"<Field: {str(e).lower()}" + f", error url: {response.url}>"
            self.logger.exception(error_info)
        except Exception as e:
            self.logger.exception(e)

    async def _process_response(self, request: Request, response: Response):
        if response:
            if response.ok:
                # Process succeed response
                self.success_counts += 1
                await self.process_succeed_response(request, response)
            else:
                # Process failed response
                self.failed_counts += 1
                await self.process_failed_response(request, response)

    async def _run_request_middleware(self, request: Request):
        if self.middleware.request_middleware:
            for middleware in self.middleware.request_middleware:
                if callable(middleware):
                    try:
                        aws_middleware_func = middleware(self, request)
                        if isawaitable(aws_middleware_func):
                            await aws_middleware_func
                        else:
                            self.logger.error(
                                f"<Middleware {middleware.__name__}: must be a coroutine function"
                            )
                    except Exception as e:
                        self.logger.exception(f"<Middleware {middleware.__name__}: {e}")

    async def _run_response_middleware(self, request: Request, response: Response):
        if self.middleware.response_middleware:
            for middleware in self.middleware.response_middleware:
                if callable(middleware):
                    try:
                        aws_middleware_func = middleware(self, request, response)
                        if isawaitable(aws_middleware_func):
                            await aws_middleware_func
                        else:
                            self.logger.error(
                                f"<Middleware {middleware.__name__}: must be a coroutine function"
                            )
                    except Exception as e:
                        self.logger.exception(f"<Middleware {middleware.__name__}: {e}")

    async def _start(self, after_start=None, before_stop=None):
        self.logger.info("Spider started!")
        start_time = datetime.now()

        # Add signal
        for signal in (SIGINT, SIGTERM):
            try:
                self.loop.add_signal_handler(
                    signal, lambda: asyncio.ensure_future(self.stop(signal))
                )
            except NotImplementedError:
                self.logger.warning(
                    f"{self.name} tried to use loop.add_signal_handler "
                    "but it is not implemented on this platform."
                )
        # Run hook before spider start crawling
        await self._run_spider_hook(after_start)

        # Actually run crawling
        try:
            await self.start_master()
        finally:
            # Run hook after spider finished crawling
            await self._run_spider_hook(before_stop)
            await self.request_session.close()
            # Display logs about this crawl task
            end_time = datetime.now()
            self.logger.info(
                f"Total requests: {self.failed_counts + self.success_counts}"
            )

            if self.failed_counts:
                self.logger.info(f"Failed requests: {self.failed_counts}")
            self.logger.info(f"Time usage: {end_time - start_time}")
            self.logger.info("Spider finished!")

    @staticmethod
    async def cancel_all_tasks():
        """
        Cancel all tasks
        :return:
        """
        tasks = []
        for task in async_all_tasks():
            if task is not async_current_task():
                tasks.append(task)
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    @classmethod
    def start(
            cls,
            middleware: typing.Union[typing.Iterable, Middleware] = None,
            loop=None,
            after_start=None,
            before_stop=None,
            close_event_loop=True,
            **spider_kwargs,
    ):
        """
        Start a spider
        :param after_start: hook
        :param before_stop: hook
        :param middleware: customize middleware or a list of middleware
        :param loop: event loop
        :param close_event_loop: bool
        :param spider_kwargs: Additional keyword args to initialize spider
        :return: An instance of :cls:`Spider`
        """
        loop = loop or asyncio.new_event_loop()
        spider_ins = cls(middleware=middleware, loop=loop, **spider_kwargs)

        str1 = spider_ins._start(after_start=after_start, before_stop=before_stop)
        spider_ins.loop.run_until_complete(str1)
        # Actually start crawling
        # spider_ins.loop.run_until_complete(
        #     spider_ins._start(after_start=after_start, before_stop=before_stop)
        # )

        spider_ins.loop.run_until_complete(spider_ins.loop.shutdown_asyncgens())
        if close_event_loop:
            spider_ins.loop.close()

        return spider_ins

    async def handle_callback(self, aws_callback: typing.Coroutine, response):
        """
        Process coroutine callback function
        """
        callback_result = None

        try:
            callback_result = await aws_callback
        except NothingMatchedError as e:
            self.logger.exception(f"<Item: {str(e).lower()}>")
        except Exception as e:
            self.logger.exception(f"<Callback[{aws_callback.__name__}]: {e}")

        return callback_result, response

    # 从此开始
    async def handle_request(
            self, request: Request
    ) -> typing.Tuple[AsyncGeneratorType, Response]:
        """
        Wrap request with middleware.
        :param request:
        :return:
        """
        callback_result, response = None, None

        try:
            # 请求中间件
            await self._run_request_middleware(request)
            # 发送请求，调用回调函数
            callback_result, response = await request.fetch_callback(self.sem)
            # 响应后中间件
            await self._run_response_middleware(request, response)
            # 统计成功，失败次数
            await self._process_response(request=request, response=response)
        except NotImplementedParseError as e:
            self.logger.exception(e)
        except NothingMatchedError as e:
            error_info = f"<Field: {str(e).lower()}" + f", error url: {request.url}>"
            self.logger.exception(error_info)
        except Exception as e:
            self.logger.exception(f"<Callback[{request.callback.__name__}]: {e}")

        return callback_result, response

    async def multiple_request(self, urls, is_gather=False, **kwargs):
        """
        For crawling multiple urls
        """
        if is_gather:
            resp_results = await asyncio.gather(
                *[self.handle_request(self.request(url=url, **kwargs)) for url in urls],
                return_exceptions=True,
            )
            for index, task_result in enumerate(resp_results):
                if not isinstance(task_result, RuntimeError) and task_result:
                    _, response = task_result
                    response.index = index
                    yield response
        else:
            for index, url in enumerate(urls):
                _, response = await self.handle_request(self.request(url=url, **kwargs))
                response.index = index
                yield response

    async def start_requests(self):
        """
        :param: start_request
        """
        for url in self.start_urls:
            yield self.request(url=url, callback=self.parse)

    async def parse(self, response):
        """
        Default callback function
        :param response: Response
        :return:
        """
        raise NotImplementedParseError("<!!! parse function is expected !!!>")

    def request(
            self,
            url: str,
            method: str = "GET",
            params=None,
            data=None,
            cookies=None,
            callback=None,
            encoding: typing.Optional[str] = None,
            headers: dict = None,
            meta: dict = None,
            request_config: dict = None,
            request_session=None,
            **aiohttp_kwargs,
    ):
        """
        Init a Request class for crawling html
        :param url:
        :param method:
        :param callback:
        :param encoding:
        :param headers:
        :param meta:
        :param request_config:
        :param request_session:
        :param aiohttp_kwargs:
        :return:
        """
        headers = headers or {}
        meta = meta or {}
        callback = callback or self.parse
        request_config = request_config or {}
        request_session = request_session or self.request_session

        request_config.update(self.request_config.copy())
        aiohttp_kwargs.update(self.aiohttp_kwargs.copy())

        return Request(
            url=url,
            method=method,
            params=params,
            data=data,
            cookies=cookies,
            callback=callback,
            encoding=encoding,
            headers=headers,
            meta=meta,
            request_config=request_config,
            request_session=request_session,
            **aiohttp_kwargs,
        )

    async def start_master(self):
        """
        Actually start crawling
        """
        async for request_ins in self.start_requests():
            self.request_queue.put_nowait(self.handle_request(request_ins))
        workers = [
            asyncio.ensure_future(self.start_worker())
            for i in range(self.worker_numbers)
        ]
        for worker in workers:
            self.logger.info(f"Worker started: {id(worker)}")
        await self.request_queue.join()

        if not self.is_async_start:
            await self.stop(SIGINT)
        else:
            if self.cancel_tasks:
                await self.cancel_all_tasks()

    async def start_worker(self):
        """
        Start spider worker
        :return:
        """
        while True:
            request_item = await self.request_queue.get()
            self.worker_tasks.append(request_item)
            if self.request_queue.empty():
                results = await asyncio.gather(
                    *self.worker_tasks, return_exceptions=True
                )
                for task_result in results:
                    if not isinstance(task_result, RuntimeError) and task_result:
                        callback_results, response = task_result
                        if isinstance(callback_results, AsyncGeneratorType):
                            await self._process_async_callback(
                                callback_results, response
                            )
                self.worker_tasks = []
            self.request_queue.task_done()

    async def stop(self, _signal):
        """
        Finish all running tasks, cancel remaining tasks.
        :param _signal:
        :return:
        """
        self.logger.info(f"Stopping spider: {self.name}")
        await self.cancel_all_tasks()
        # self.loop.stop()
