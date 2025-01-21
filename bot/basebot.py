#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# bot/basebot.py
# 机器人基础功能
import logging
import time

from wcferry import Wcf, WxMsg
from .configuration import Config
from .job_mgmt import Job


class Basebot(Job):

    # def __init__(self, wcf: Wcf, chat_type: int) -> None:
    def __init__(self, config: Config, wcf: Wcf) -> None:
        self.wcf = wcf
        self.config = config
        self.LOG = logging.getLogger("Bot")
        self.wxid = self.wcf.get_self_wxid()
        self.allContacts = self.getAllContacts()

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
