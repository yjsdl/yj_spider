#!/usr/bin/env python

import re

from typing import Union

from lxml import etree

from Yjsdl.exceptions import NothingMatchedError


class BaseField(object):
    """
    BaseField class
    """

    def __init__(self, default="", many: bool = False):
        """
        Init BaseField class
        url: http://lxml.de/index.html
        :param default: default value
        :param many: if there are many fields in one page
        """
        self.default = default
        self.many = many

    def extract(self, *args, **kwargs):
        raise NotImplementedError("Extract is not implemented.")


class CsvFile:
    name = 'csv file'


    def __init__(self, ):
        pass
    # async def CsvFile(cls, filename: list = None, data: list = None):
    #     async with aiofiles.open("new_file2.csv", mode="w", encoding="utf-8", newline="") as afp:
    #         if filename is None:
    #             raise ValueError('please input file headers')
    #         writer = AsyncDictWriter(afp, filename, restval="NULL", quoting=csv.QUOTE_ALL)
    #         await writer.writeheader()
    #         await writer.writerows(data)

