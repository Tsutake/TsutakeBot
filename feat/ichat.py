#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# feat.ichat feat包
# LLM模型接入
import ollama

from wcferry import Wcf, WxMsg
from bot.basebot import Basebot
from bot.configuration import Config


class ichat(Basebot):
    def __init__(self, conf: dict) -> None:
        # super().__init__(config, wcf)
        self.model = conf.get("model", "")
        self.ollama = ollama.Client()


if __name__ == "__main__":
    config = Config().ichat
    if not config:

        exit(1)
