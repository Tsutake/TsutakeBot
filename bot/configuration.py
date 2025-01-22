#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# config配置类
import os
import shutil
from ruamel.yaml import YAML


class Config:
    def __init__(self) -> None:
        # 获取当前脚本运行处于的绝对目录
        self.pwd = os.path.dirname(os.path.abspath(__file__))
        self.template_path = os.path.join(self.pwd, "../conf", "config.yaml.template")
        self.config_path = os.path.join(self.pwd, "../conf", "config.yaml")
        self.yaml = YAML()
        self.yaml.preserve_quotes = True  # 保留引号
        self.yaml.width = 4096  # 设置宽度，避免自动换行
        self.reload()

    def load_yaml(self, file_path) -> dict:
        """
        加载配置文件，用于动态更新config
        """
        with open(file_path, "r", encoding="utf-8") as f:
            return self.yaml.load(f) or {}

    def save_yaml(self, data, file_path) -> None:
        """
        保存 YAML 文件
        """
        with open(file_path, "w", encoding="utf-8") as f:
            self.yaml.dump(data, f)

    def merge_configs(self, template, existing) -> dict:
        """
        递归合并配置
        """
        if isinstance(template, dict) and isinstance(existing, dict):
            for key, value in template.items():
                if key not in existing:
                    existing[key] = value  # 添加新字段
                else:
                    # 递归合并子字段
                    self.merge_configs(value, existing[key])
        return existing

    def update_config(self) -> None:
        """
        更新配置文件
        """
        # 加载模板和现有配置
        template = self.load_yaml(self.template_path)
        existing = self.load_yaml(self.config_path)

        # 合并配置
        updated_config = self.merge_configs(template, existing)

        # 保存更新后的配置
        self.save_yaml(updated_config, self.config_path)

    def remake_config(self) -> str:
        """
        重新生成配置文件
        """
        try:
            os.remove(self.config_path)
        except FileNotFoundError:
            res = f"文件 {self.config_path} 不存在."
            return res
        except Exception as e:
            res = f"产生报错： {self.config_path}: {e}"
            return res
        self.reload()
        res = "配置文件重制成功"
        return res


    def _load_config(self) -> dict:
        """
        装载配置文件
        :return:配置字典
        """
        try:
            self.update_config()
            with open(self.config_path, "r", encoding="utf-8") as fp:
                return self.yaml.load(fp) or {}
        except FileNotFoundError:
            # 如果 config.yaml 不存在，则从模板创建
            shutil.copyfile(self.template_path, self.config_path)
            with open(self.template_path, "r", encoding="utf-8") as fp:
                return self.yaml.load(fp) or {}

    def reload(self) -> None:
        """
        重载配置文件
        """
        yconfig = self._load_config()
        # 基础配置文件
        self.GROUPS = yconfig["groups"]["enable"]
        self.NEWS = yconfig["news"]["receivers"]
        self.REPORT_REMINDERS = yconfig["report_reminder"]["receivers"]
        self.Rootusr = yconfig["rootusr"]["username"]

        # API配置文件
        self.ichat = yconfig.get("ichat", {})
        self.DBserver = yconfig.get("DBserver", {})
        self.API = yconfig.get("API", {})


if __name__ == "__main__":
    config = Config()
    print(config)
