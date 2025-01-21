#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 工具类
import os
import re
import pandas as pd

from datetime import datetime
from wcferry import Wcf


class Utils(object):

    def __init__(self, wcf: Wcf) -> None:
        self.wcf = wcf
        pass

    def GetContactsonLocal(self) -> None:
        """
        获取所有的联系人的wxid到本地Excel文件
        保存至toolfile目录下的contacts目录中
        :return:None
        """
        contacts = self.wcf.query_sql("MicroMsg.db", "SELECT UserName, NickName FROM Contact;")
        # 将 contacts 转换为 DataFrame
        df = pd.DataFrame(contacts)
        # 获取当前时间并格式化
        current_time = datetime.now()
        # 格式化为【月日-小时分钟】
        formatted_time = current_time.strftime("%m%d-%H%M")
        # 构造文件名
        folder_name_1 = 'toolfiles'  # 文件夹一级目录名称
        folder_name_2 = 'contactsfiles'  # 文件夹二级目录名称
        file_name = f'contacts-{formatted_time}.xlsx'
        file_path = os.path.join(folder_name_1, folder_name_2, file_name)
        # 输出到 Excel 文件
        df.to_excel(file_path, index=False, columns=["UserName", "NickName"])
        return

    def SendTestText(self) -> None:
        """
        发送测试文本消息
        :return:None
        """
        current_time = datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        msg = f"于{formatted_time}连接成功！"
        self.wcf.send_text(f"{msg}", "filehelper", "")
        return

    def ReadDates(self, match) -> list:
        """
        提取匹配到的日期
        """
        if match:
            # 获取第一次匹配的日期
            dates = [match.group(1)]

            # 在原字符串中查找所有额外的日期
            # 使用全部匹配
            additional_dates = re.findall(r'\d{8}', match.string)
            # 排除已经匹配的第一个日期
            return dates + [date for date in additional_dates if date != dates[0]]
        return []



