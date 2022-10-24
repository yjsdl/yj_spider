# -*- coding: utf-8 -*-
# @Time    : 2022/8/22 17:31
# @Author  : Liuyijie
# @File    : item.py
from collections import UserList
import os
from inspect import isawaitable
from typing import Any
from lxml import etree
from aiocsv import AsyncDictWriter
import csv
import aiofiles
from Yjsdl.exceptions import IgnoreThisItem, InvalidFuncType
from Yjsdl import field
from Yjsdl.request import Request


class ItemMeta(type):
    """
    Metaclass for an item
    """

    def __new__(cls, name, bases, attrs):
        __fields = dict(
            {
                (field_name, attrs.pop(field_name))
                for field_name, object in list(attrs.items())
                if isinstance(object, field.BaseField)
            }
        )
        attrs["__fields"] = __fields
        new_class = type.__new__(cls, name, bases, attrs)
        return new_class


class Item:
    """
    仅占用一个类型
    """
    data = None

    def __len__(self): return len(self.data)

    def __contains__(self, item): return item in self.data

    def __setitem__(self, i, item): self.data[i] = item

    def __str__(self): return self.data

    def __repr__(self): return repr(self.data)

    def __iter__(self):
        for obj in self.data if type(self.data) is dict else self.data.items():
            yield obj


# class Item(metaclass=ItemMeta):
#     """
#     Item class for each item
#     """
#
#     def __init__(self):
#         self.ignore_item = False
#         self.results = {}
#
#     @classmethod
#     async def get_resp(cls, html: str = "", url: str = "", **kwargs):
#         if html and url:
#             raise ValueError("<Item: html *or* url expected, not both.")
#         if html or url:
#             if url:
#                 async with aiohttp.ClientSession() as session:
#                     sem = kwargs.pop("sem", None)
#                     request = Request(url, request_session=session, **kwargs)
#                     if sem:
#                         _, response = await request.fetch_callback(sem=sem)
#                     else:
#                         response = await request.fetch()
#                     # if types == "" or types == 'text':
#                     #     html = await response.text()
#                     # elif types == 'json':
#                     #     html = await response.json()
#                     # else:
#                     #     html = await response.read()
#             return response
#         else:
#             raise ValueError("<Item: html(url or html_etree) is expected.")
#
#     @classmethod
#     async def _get_html(cls, html: str = "", url: str = "", **kwargs):
#         if html and url:
#             raise ValueError("<Item: html *or* url expected, not both.")
#         if html or url:
#             if url:
#                 async with aiohttp.ClientSession() as session:
#                     sem = kwargs.pop("sem", None)
#                     request = Request(url, request_session=session, **kwargs)
#                     if sem:
#                         _, response = await request.fetch_callback(sem=sem)
#                     else:
#                         response = await request.fetch()
#                     # HTMl
#                     html = await response.text()
#             return etree.HTML(html)
#         else:
#             raise ValueError("<Item: html(url or html_etree) is expected.")
#
#     @classmethod
#     async def _parse_html(cls, *, html_etree: etree._Element):
#         if html_etree is None:
#             raise ValueError("<Item: html_etree is expected>")
#         item_ins = cls()
#         fields_dict = getattr(item_ins, "__fields", {})
#         for field_name, field_value in fields_dict.items():
#             if not field_name.startswith("target_"):
#                 clean_method = getattr(item_ins, f"clean_{field_name}", None)
#                 value = field_value.extract(html_etree)
#                 if clean_method is not None and callable(clean_method):
#                     try:
#                         aws_clean_func = clean_method(value)
#                         if isawaitable(aws_clean_func):
#                             value = await aws_clean_func
#                         else:
#                             raise InvalidFuncType(
#                                 f"<Item: clean_method must be a coroutine function>"
#                             )
#                     except IgnoreThisItem:
#                         item_ins.ignore_item = True
#
#                 setattr(item_ins, field_name, value)
#                 item_ins.results[field_name] = value
#         return item_ins
#
#     @classmethod
#     async def get_item(
#             cls,
#             *,
#             html: str = "",
#             url: str = "",
#             html_etree: etree._Element = None,
#             **kwargs,
#     ) -> Any:
#         if html_etree is None:
#             html_etree = await cls._get_html(html, url, **kwargs)
#
#         return await cls._parse_html(html_etree=html_etree)
#
#     @classmethod
#     async def get_items(
#             cls,
#             *,
#             html: str = "",
#             url: str = "",
#             html_etree: etree._Element = None,
#             **kwargs,
#     ):
#         if html_etree is None:
#             html_etree = await cls._get_html(html, url, **kwargs)
#         items_field = getattr(cls, "__fields", {}).get("target_item", None)
#         if items_field:
#             items_field.many = True
#             items_html_etree = items_field.extract(
#                 html_etree=html_etree, is_source=True
#             )
#             if items_html_etree:
#                 for each_html_etree in items_html_etree:
#                     item = await cls._parse_html(html_etree=each_html_etree)
#                     if not item.ignore_item:
#                         yield item
#             else:
#                 value_error_info = "<Item: Failed to get target_item's value from"
#                 if url:
#                     value_error_info = f"{value_error_info} url: {url}.>"
#                 if html:
#                     value_error_info = f"{value_error_info} html.>"
#                 raise ValueError(value_error_info)
#         else:
#             raise ValueError(
#                 f"<Item: target_item is expected"
#             )
#
#     def __repr__(self):
#         return f"<Item {self.results}>"


class MyArray(UserList):
    # 继承自 UserList, 修改 __init__ 以支持传参
    def __init__(self, initlist=None, **kwargs):
        super().__init__()
        self.data = []
        if initlist is not None:
            # XXX should this accept an arbitrary sequence?
            if type(initlist) == type(self.data):
                self.data[:] = initlist
            elif isinstance(initlist, UserList):
                self.data[:] = initlist.data[:]
            else:
                self.data = list(initlist)
        for key, val in kwargs.items():
            self.__dict__[key] = val


class CsvItem(MyArray, Item):
    name = 'CsvFile'
    data_storage: str = None
    mode: str = "a"
    filetype: str = 'csv'
    filename: str = None
    __file_header = None
    is_header = False
    encoding: str = 'utf-8'

    def __init__(
            self, data_storage=None, mode=None, filename=None, file_header=None, encoding=None,
            initlist=None, **kwargs
    ):
        super().__init__(initlist=initlist, **kwargs)
        self.data_storage = data_storage
        self.filename = str(filename)
        if mode:
            self.mode = mode
        if encoding:
            self.encoding = encoding
        if os.path.exists(self.data_storage + '/' + f"{self.filename}.{self.filetype}"):
            self.is_header = True
        self.__file_header = file_header or (self[0].keys() if len(self) else None)

    @property
    def file_header(self):
        if self.__file_header is None:
            self.__file_header = self[0].keys() if len(self) else []
        return self.__file_header

    @file_header.setter
    def file_header(self, val):
        if self.__file_header != val:
            self.__file_header = val

    def set_attribute(self,
                      data_storage=None,
                      filename=None,
                      mode=None,
                      encoding=None,
                      file_header=None, **kwargs):
        self.data_storage = data_storage
        self.filename = filename
        self.mode = mode or self.mode
        self.encoding = encoding or self.encoding
        self.file_header = file_header or self[0].keys() if len(self) else []
