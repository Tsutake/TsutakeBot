#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# config配置类
import os
import shutil
import yaml


class Config():
    def __init__(self) -> None:
        self.reload()

    def _load_cofig(self) -> dict:
        # 获取当前脚本运行处于的绝对目录
        pwd = os.path.dirname(os.path.abspath(__file__))
        tempyaml = os.path.join(pwd, "../conf", "config.yaml.template")
        nyaml = os.path.join(pwd, "../conf", "config.yaml")
        try:
            with open(f"{nyaml}", "rb") as fp:
                yconfig = yaml.safe_load(fp)
        # 若config.yaml文件不存在，则创建一个config.yaml文件
        except FileNotFoundError:
            # 将config.yaml.template文件复制到config.yaml文件
            shutil.copyfile(f"{tempyaml}", f"{nyaml}")
            with open(f"{tempyaml}", "rb") as fp:
                yconfig = yaml.safe_load(fp)

        return yconfig

    def reload(self) -> None:
        # 装载配置文件
        yconfig = self._load_cofig()
        # 基础配置文件
        self.GROUPS = yconfig["groups"]["enable"]
        self.NEWS = yconfig["news"]["receivers"]
        self.REPORT_REMINDERS = yconfig["report_reminder"]["receivers"]
        self.Rootusr = yconfig["rootusr"]["username"]

        # API配置文件
        # self.ichat = yconfig("ichat", {})
