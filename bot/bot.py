#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 机器人主要功能
import logging
import time

from queue import Empty
from threading import Thread
from wcferry import Wcf, WxMsg
from .configuration import Config
from .job_mgmt import Job


class Bot(Job):
    # def __init__(self, wcf: Wcf, chat_type: int) -> None:
    def __init__(self, config: Config, wcf: Wcf) -> None:
        # super().__init__()
        self.wcf = wcf
        self.config = config
        self.LOG = logging.getLogger("Bot")
        self.wxid = self.wcf.get_self_wxid()
        self.allContacts = self.getAllContacts()

    def sendTextMsg(self, msg: str, receiver: str, at_list: str = "") -> None:
        """ 发送消息
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

    def processMsg(self, msg: WxMsg) -> None:
        """
        当接收到消息的时候，会调用本方法。如果不实现本方法，则打印原始消息。
        self.sendTextMsg(content, receivers, msg.sender)
        """
        # 群聊消息
        if msg.from_group():
            # 如果在群里被 @
            if msg.roomid not in self.config.GROUPS:  # 不在配置的响应的群列表里，忽略
                return

            if msg.is_at(self.wxid):  # 被@
                self.toAt(msg)

            else:  # 其他消息
                # self.toChengyu(msg)
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
            if msg.from_self():
                if msg.content == "^更新$":
                    self.config.reload()
                    self.LOG.info("已更新")
                    self.wcf.send_text("更新配置成功", "TsutakeMini", "")
            else:
                self.TempReply(msg)  # 闲聊

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

    def toAt(self, msg: WxMsg) -> None:
        """处理被 @ 消息
        :param msg: 微信消息结构
        :return: 处理状态，`True` 成功，`False` 失败
        """
        self.TempReply(msg)

    def getAllContacts(self) -> dict:
        """
        获取所有联系人（包括好友、公众号、服务号、群成员……）
        格式: {"wxid": "NickName"}
        :return :contacts
        """
        contacts = self.wcf.query_sql("MicroMsg.db", "SELECT UserName, NickName FROM Contact;")
        return {contact["UserName"]: contact["NickName"] for contact in contacts}

    def KeepRunning(self) -> None:
        """
        保持bot持续运行不退出
        :return: None
        """
        while True:
            self.runPendingJobs()
            time.sleep(1)
