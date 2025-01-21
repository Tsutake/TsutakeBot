#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# main类
import signal

from wcferry import Wcf
from bot.bot import Bot
from gutils.utils import Utils
from bot.configuration import Config


def main():
    config = Config()
    wcf = Wcf(debug=True)

    def handler(sig, frame):
        wcf.cleanup()  # 退出前清理环境
        exit(0)
    signal.signal(signal.SIGINT, handler)

    # 工具功能开启
    BotUtils = Utils(wcf)
    BotUtils.SendTestText()  # 发送测试文本
    # 获取所有联系人到本地Excel文件中
    # BotUtils.GetContactsonLocal()

    # bot功能开启
    bot = Bot(config, wcf)
    bot.enableReceivingMsg()  # 加队列
    bot.KeepRunning()  # 保持程序运行


if __name__ == "__main__":
    # parser = ArgumentParser()
    # parser.add_argument('-c', type=int, default=0)
    # args = parser.parse_args().c
    main()
