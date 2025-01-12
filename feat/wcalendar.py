#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# feat.wcalendar feat包
# 万年历功能
"""
接口返回参数说明：
date : 日期
weekDay : 当前周第几天，1-周一、2-周二、3-周三、4-周四、5-周五、6-周六、7-周日
yearTips : 天干地支纪年法
type : 0-工作日、1-假日、2-节假日
detailsType : 0-工作日、1-假日、2-节假日、3-三倍工资节假日
typeDes : 类型描述，如：国庆、休息日、工作日
chineseZodiac : 属相
solarTerms : 节气
avoid  : 忌
lunarCalendar : 农历日历
suit : 宜
dayOfYear : 这一年的第几天
weekOfYear : 这一年的第几周
constellation : 星座
indexWorkDayOfMonth : 如果是工作日，则返回这是当月的第几个工作日，否则返回0
"""
import requests
import json

from typing import Union, Any, Dict
from datetime import datetime


class WCalendar(object):
    def __init__(self, ):
        self.base_url = "https://www.mxnzp.com/api/holiday/"
        self.params = {
            "app_id": "embeakg1jhojulyh",
            "app_secret": "3MTSJ0bF0ppLUPqaifiMgDzWIa7rgzw0"
        }
        pass

    def GetWcalendar(self, date: str, api: str, status: int, **kwargs) -> str:
        """
        获取指定日期的万年历信息
        :return:万年历信息
        """
        url = self.base_url + api + date
        params = self.params
        params.update(kwargs)
        response = requests.get(url, params=params)
        # 判断请求是否成功
        if response.status_code == 200:
            # 处理数据 JSON 数据
            res = self.AnswerStr(response.json(), status)
            # 返回 JSON 格式的响应
            # return response.json()
            return res
        else:
            # 返回状态码和错误信息
            res = f"请求失败，状态码：{response.status_code}, 错误信息：{response.text}"
            return res

    def AnswerStr(self, calendar: dict, status: int) -> str:
        """
        处理接受的json信息，并且根据状态码返回不同的回复
        :return: 回复字符串
        """
        try:
            if calendar["code"] == 1:
                data = calendar["data"]
                if status == 1:  # 今日黄历
                    dictprocess = self.dictProcess(calendar)  # 字典数据处理
                    date = datetime.strptime(data["date"], "%Y-%m-%d")  # 日期
                    res = (f"今天是{date.year}年{date.month}月{date.day}日，"
                           f"{data['yearTips']}{data['chineseZodiac']}年{data['lunarCalendar']},"
                           f"{dictprocess.get('weekDay')}。"
                           f"\n今日节气为{data['solarTerms']}"
                           f"\n宜:{data['suit'].replace('.', '、')}"
                           f"\n忌:{data['avoid'].replace('.', '、')}。"
                           f"\n今日星座为{data['constellation']}，"
                           )
                    if data['indexWorkDayOfMonth'] > 0:
                        res += f"是这个月第{data['indexWorkDayOfMonth']}个工作日。"
                    else:
                        res += f"是休息的一天。"

                elif status == 2:  # 指定日期黄历
                    dictprocess = self.dictProcess(calendar) # 字典数据处理
                    date = datetime.strptime(data["date"], "%Y-%m-%d")  # 日期
                    res = (f"{date.year}年{date.month}月{date.day}日，"
                           f"为{data['yearTips']}{data['chineseZodiac']}年{data['lunarCalendar']}"
                           f"{dictprocess.get('weekDay')}。\n"
                           f"当日节气为{data['solarTerms']}\n"
                           f"宜:{data['suit'].replace('.', '、')}\n"
                           f"忌:{data['avoid'].replace('.', '、')}。\n"
                           f"当日星座为{data['constellation']}，"
                           )
                    if data['indexWorkDayOfMonth'] > 0:
                        res += f"是这个月第{data['indexWorkDayOfMonth']}个工作日。"
                    else:
                        res += f"是休息的一天。"
                elif status == 3:  # 多个日期黄历
                    dictprocess = self.dictProcess(calendar)  # 字典数据处理
                    res = ''
                    for i in range(len(data)):
                        date = datetime.strptime(data[i]["date"], "%Y-%m-%d")
                        res += (f"\n{date.year}年{date.month}月{date.day}日，"
                                f"为{data['yearTips']}{data['chineseZodiac']}年{data['lunarCalendar']}"
                                f"{dictprocess.get('weekDay')}。\n"
                                f"当日节气为{data['solarTerms']}\n"
                                f"宜:{data['suit'].replace('.', '、')}\n"
                                f"忌:{data['avoid'].replace('.', '、')}。\n"
                                f"当日星座为{data['constellation']}，"
                                )
                        if data['indexWorkDayOfMonth'] > 0:
                            res += f"是这个月第{data['indexWorkDayOfMonth']}个工作日。"
                        else:
                            res += f"是休息的一天。"
                else:
                    res = "功能开发中^_^"
            else:
                res = "请求失败"
        # 异常抛出模块
        except json.JSONDecodeError:
            res = "JSON 格式错误。"
        except KeyError as e:
            res = f"缺少必要的字段: {str(e)}"
        return res

    def dictProcess(self, calendar: dict) -> dict:
        """
        字典处理，处理收到的 JSON 信息中的字典数据
        :return: 将处理好的字典数据
        """
        res = {}
        data = calendar["data"]
        # 星期字典
        weekDayMapping = {
            1: "星期一",
            2: "星期二",
            3: "星期三",
            4: "星期四",
            5: "星期五",
            6: "星期六",
            7: "星期日"
        }
        # 工作性质字典
        typeMapping = {
            0: "工作日",
            1: "假日",
            2: "节假日"
        }
        # 节日字典
        detailsMapping = {
            0: "工作日",
            1: "假日",
            2: "节假日",
            3: "三倍工资节假日"
        }
        res['weekDay'] = weekDayMapping.get(data["weekDay"], "未知星期")
        res['type'] = typeMapping.get(data["type"], "未知类型")
        res['detailsType'] = detailsMapping.get(data["detailsType"], "未知详细类型")
        return res