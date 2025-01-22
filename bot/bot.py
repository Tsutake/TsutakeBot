#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# bot/bot.py
# 机器人主要功能
import datetime
import re

from queue import Empty
from threading import Thread
from wcferry import Wcf, WxMsg
from typing import Union, Any, Dict
from .basebot import Basebot
from .configuration import Config
from feat.wcalendar import WCalendar
from feat.ichat import ichat
from gutils.utils import Utils


class Bot(Basebot):

    # def __init__(self, wcf: Wcf, chat_type: int) -> None:
    def __init__(self, config: Config, wcf: Wcf) -> None:
        super().__init__(config, wcf)
        self.utils = Utils(self.wcf)  # 启用工具类
        self.wnl = WCalendar(config)  # 启用万年历功能

    def ReplyRecognition(self, msg: WxMsg) -> str:
        """
        回复识别
        功能：万年历,调用GetWcalendar(date, status, **kwargs)函数来获取黄历信息
        date: 传入需要查询的日期
        status: 1-今日黄历, 2-指定日期黄历, 3-多个日期黄历
        kwargs: 额外参数，默认需要传入ignoreHoliday="False"
        :return 组装好的文本消息
        """
        if '今日黄历' in msg.content:  # 今日黄历
            # date = "20250108" # 测试
            # 获取当日日期
            today = datetime.date.today()
            # 格式化日期
            date = today.strftime("%Y%m%d")
            resmsg = self.wnl.GetWcalendar(date, 'single/', 1, ignoreHoliday="False")

        elif '查询黄历' in msg.content:  # 指定日期黄历
            # 正则匹配
            pattern_1 = "查询黄历[：:](\d{8})"  # 匹配'查询黄历'
            match_1 = re.search(pattern_1, msg.content)
            if match_1:
                pattern_2 = r"查询黄历[：:](\d{8})(?:[，,](\d{8}))*"  # 匹配多个日期
                match_2 = re.search(pattern_2, msg.content)
                if match_2:
                    dates = self.utils.ReadDates(match_2)  # 提取日期
                    if len(dates) == 1:  # 只有一个日期 -> 查询指定黄历
                        date = dates[0]
                        resmsg = self.wnl.GetWcalendar(date, 'single/', 2, ignoreHoliday="False")
                    else:  # 多个日期 -> 查询多个黄历
                        date_str = dates[0]
                        for i in range(1, len(dates)+1):
                            date_str += ',' + dates[i]
                        resmsg = self.wnl.GetWcalendar(date_str, 'multi/', 3, ignoreHoliday="False")
                else:
                    resmsg = "若想获得多个日期，请输入正确格式，例如：查询黄历：20250108，20250109"
            else:
                resmsg = "请输入正确的日期格式，例如：查询黄历：20250108"

        elif '获取群id' in msg.content:  # 获取当前群id
            if msg.sender in self.config.Rootusr:
                self.sendTextMsg(f"群id为：{msg.roomid}", msg.sender)
                resmsg = "已私发群id"
            else:
                resmsg = "权限不足！"
        else:
            # 待开发功能
            resmsg = '功能开发中^_^'

        return resmsg

    def processMsg(self, msg: WxMsg) -> None:
        """
        当接收到消息的时候，会调用本方法。如果不实现本方法，则打印原始消息。
        self.sendTextMsg(content, receivers, msg.sender)
        """
        # 群聊消息
        if msg.from_group():
            # 如果在群里被 @
            if msg.roomid not in self.config.GROUPS:  # 不在配置的响应的群列表里，忽略
                if '获取群id' in msg.content and msg.sender in self.config.Rootusr:
                    self.sendTextMsg(f"群id为：{msg.roomid}", msg.sender)
                    self.sendTextMsg("已私发群id", msg.roomid, msg.sender)
                    return
                else:
                    return

            if msg.is_at(self.wxid):  # 被@
                # return
                self.toAt(msg)

            else:  # 其他消息
                pass

            return  # 处理完群聊信息，后面就不需要处理了

        # 非群聊信息，按消息类型进行处理
        if msg.type == 37:  # 好友请求
            # self.autoAcceptFriendRequest(msg)
            pass

        elif msg.type == 10000:  # 系统信息
            # self.sayHiToNewFriend(msg)
            pass

        if msg.type == 0x01:  # 文本消息
            if msg.from_self():  # 来自自己的消息
                self.fromSelf(msg)

            else:
                res = self.ReplyRecognition(msg)  # 私聊的回复
                if res == "功能开发中^_^":
                    chat = ichat(self.config, msg.sender, msg.content)
                    self.sendTextMsg(chat.iChatWithLLM(), msg.sender)
                else:
                    self.sendTextMsg(res, msg.sender)

    def enableReceivingMsg(self) -> None:
        """
        开启接收消息，创建GetMessage守护线程，目标函数为innerProcessMsg()
        :return: None
        """

        def innerProcessMsg(wcf: Wcf):
            while wcf.is_receiving_msg():
                try:
                    msg = wcf.get_msg()
                    self.LOG.info(msg)
                    self.processMsg(msg)
                except Empty:
                    continue  # 检测到空异常则跳过，检测到其他异常则日志打印异常
                except Exception as e:
                    self.LOG.error(f"Receiving message error: {e}")

        # 开启接收消息
        self.wcf.enable_receiving_msg()
        # 创建守护线程
        Thread(target=innerProcessMsg, name="GetMessage", args=(self.wcf,), daemon=True).start()

    def sendTextMsg(self, msg: str, receiver: str, at_list: str = "") -> None:
        """ 发送消息
        发送个人消息格式为sendTextMsg(msg, msg.sender)
        发送群消息格式为sendTextMsg(msg, msg.roomid, msg.sender)
        :param msg: 消息字符串
        :param receiver: 接收人wxid或者群id
        :param at_list: 要@的wxid, @所有人的wxid为：notify@all
        """
        # msg 中需要有 @ 名单中一样数量的 @
        ats = ""
        if at_list:
            if at_list == "notify@all":  # @所有人
                ats = " @所有人"
            else:
                wxids = at_list.split(",")
                for wxid in wxids:
                    # 根据 wxid 查找群昵称
                    ats += f" @{self.wcf.get_alias_in_chatroom(wxid, receiver)}"

        # {msg}{ats} 表示要发送的消息内容后面紧跟@，例如 北京天气情况为：xxx @张三
        if ats == "":
            self.LOG.info(f"To {receiver}: {msg}")
            self.wcf.send_text(f"{msg}", receiver, at_list)
        else:
            self.LOG.info(f"To {receiver}: {ats}\r{msg}")
            self.wcf.send_text(f"{ats} {msg}", receiver, at_list)

    def toAt(self, msg: WxMsg) -> bool:
        """处理被 @ 消息
        :return:
        """
        res = self.ReplyRecognition(msg)  # 被@的回复
        if res == "功能开发中^_^":
            chat = ichat(self.config, msg.sender, msg.content, msg.roomid)
            self.sendTextMsg(chat.iChatWithLLM(), msg.roomid, msg.sender)
        else:
            self.sendTextMsg(res, msg.roomid, msg.sender)
        return True

    def fromSelf(self, msg: WxMsg) -> bool:
        """
        处理来自自己的消息
        :return:
        """
        if msg.content in ["help", "帮助"]:
            help_messages = ("你好哦～以下管理员权限指令:\n"
                             "^更新配置$ 可以重新装载配置文件\n"
                             "^更新模板$ 可以重新把新模板的内容更新至配置文件\n"
                             "^重制配置文件$ 可以重新生成配置文件\n")
            self.wcf.send_text(help_messages, "TsutakeMini", "")
        elif msg.content == "^更新配置$":
            self.config.reload()
            self.LOG.info("已更新配置")
            self.wcf.send_text("更新配置成功", "TsutakeMini", "")
        elif msg.content == "^更新模板$":
            self.config.update_config()
            self.LOG.info("已更新模板")
            self.wcf.send_text("更新模板成功", "TsutakeMini", "")
        elif msg.content == "^重制配置文件$":
            self.config.remake_config()
            self.LOG.info("已重制配置文件")
            self.wcf.send_text("重制配置文件成功", "TsutakeMini", "")
        return True

    def TempReply(self, msg: WxMsg) -> None:
        """
        临时消息回复功能
        """
        tmp = msg.content
        parts = tmp.split(' ', 1)
        rsp = msg.content
        if msg.from_group():
            self.sendTextMsg(parts[1], msg.roomid, msg.sender)
        else:
            self.sendTextMsg(rsp, msg.sender)
