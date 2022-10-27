# -*- coding: utf-8 -*-
# @Time    : 2022/8/22 17:31
# @Author  : Liuyijie
# @File    : field.py
import os

import aiofiles
import csv
from aiocsv import AsyncDictWriter
from Yjsdl.item import CsvItem
from Yjsdl.exceptions import NothingMatchedError


class BaseField(object):
    """
    BaseField class
    """

    def __init__(self, default=""):
        """
        Init BaseField class
        url: http://lxml.de/index.html
        :param default: default value
        :param many: if there are many fields in one page
        """
        self.default = default


class CsvFile:

    def __init__(self):
        self.writer = False

    async def process_item(self, item: CsvItem):
        filename = item.filename
        file_path = item.data_storage
        file = f"{filename}.{item.filetype}"
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        mode = item.mode
        file_header = item.file_header
        is_header = item.is_header

        async with aiofiles.open(file_path + '/' + file, mode=mode, encoding="utf-8", newline="") as afp:
            self.writer = AsyncDictWriter(afp, file_header, restval="NULL", quoting=csv.QUOTE_ALL)

            if not is_header:
                await self.writer.writeheader()
            await self.writer.writerows(item)
