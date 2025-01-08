#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# Utils.wcalendar Utils包
# 万年历功能
import requests

from typing import Union, Any, Dict


class WCalendar(object):
    def __init__(self,):
        self.base_url = "https://www.mxnzp.com/api/holiday/single/"
        self.params = {
            "app_id": "embeakg1jhojulyh",
            "app_secret": "3MTSJ0bF0ppLUPqaifiMgDzWIa7rgzw0"
        }
        pass

    def GetWcalendar(self, date: str, **kwargs) -> Union[Dict[str, Any], str]:
        """
        获取指定日期的万年历信息
        :return:
        """
        url = self.base_url + date
        params = self.params
        params.update(kwargs)
        response = requests.get(url, params=params)
        # 判断请求是否成功
        if response.status_code == 200:
            # 返回 JSON 格式的响应
            return response.json()
        else:
            # 返回状态码和错误信息
            res = f"请求失败，状态码：{response.status_code}, 错误信息：{response.text}"
            return res

