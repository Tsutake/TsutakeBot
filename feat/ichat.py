#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# feat.ichat feat包
# LLM模型接入
import ollama
import mysql.connector
from datetime import datetime
from dateutil import parser
from bot.configuration import Config


class ichat:

    def __init__(self, config: Config, wxid, userinput, roomid='NO_ROOM'):
        # 数据库配置
        self.config = config
        self.DB_CONFIG = {}
        self.DB_CONFIG.update(self.config.DBserver)  # 用 config.DBserver 覆盖默认值
        self.DB_CONFIG["password"] = str(self.DB_CONFIG["password"])  # 确保 password 是字符串

        self.CreateTables()
        self.wxid = wxid
        self.userinput = userinput
        self.roomid = roomid

    def GetDBConnection(self):
        """
        获取数据库连接
        """
        return mysql.connector.connect(**self.DB_CONFIG)

    def CreateTables(self):
        """
        创建表
        """
        conn = self.GetDBConnection()
        cursor = conn.cursor()

        # 创建 chat_messages_ 表 用于装载用户消息
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages_ (
                    ID_ INT AUTO_INCREMENT PRIMARY KEY,
                    MESSAGE_ROLE_ VARCHAR(50),
                    MESSAGE_CONTENT_ TEXT,
                    WXID_ VARCHAR(255),
                    ROOMID_ VARCHAR(255),
                    CREATED_TIME_ DATETIME
            )
        """)

        # 创建 chat_responses_ 表 用于记录所有的数据
        cursor.execute("""
               CREATE TABLE IF NOT EXISTS chat_responses_  (
                    ID_ INT AUTO_INCREMENT PRIMARY KEY,
                    MODEL_ VARCHAR(255),
                    CREATED_AT_ DATETIME,
                    DONE_ TINYINT,
                    DONE_REASON_ VARCHAR(255),
                    TOTAL_DURATION_ BIGINT,
                    LOAD_DURATION_ BIGINT,
                    PROMPT_EVAL_COUNT_ BIGINT ,
                    PROMPT_EVAL_DURATION_ BIGINT,
                    EVAL_COUNT_ BIGINT, 
                    EVAL_DURATION_ BIGINT,
                    MESSAGE_ROLE_ TEXT,
                    MESSAGE_CONTENT_ TEXT,
                    MESSAGE_IMAGES_ TINYINT, 
                    MESSAGE_TOOL_CALLS_ TINYINT,
                    ROOMID_ VARCHAR(255),
                    WXID_ VARCHAR(255) 
                );
           """)

        # 创建 chat_responses_backup_ 表 用于备份用户历史消息
        cursor.execute("""
              CREATE TABLE IF NOT EXISTS chat_messages_backup_ (
                    ID_ INT AUTO_INCREMENT PRIMARY KEY,
                    MESSAGE_ROLE_ VARCHAR(50),
                    MESSAGE_CONTENT_ TEXT,
                    WXID_ VARCHAR(255),
                    ROOMID_ VARCHAR(255),
                    CREATED_TIME_ DATETIME
            )
          """)

        # 创建 user_context_status 表 用于记录用户上下文是否被清除
        # cursor.execute("""
        #       CREATE TABLE IF NOT EXISTS user_context_status_ (
        #             WXID_ VARCHAR(255) PRIMARY KEY,
        #             ROOMID_  VARCHAR(255),
        #             CONTEXT_CLEARED_ BOOLEAN DEFAULT FALSE
        #       )
        #   """)

        conn.commit()
        cursor.close()
        conn.close()

    def SaveResponses(self, chat: dict):
        """
        保存模型返回记录，作用于responses表
        """
        conn = self.GetDBConnection()
        cursor = conn.cursor()

        # 插入语句构建
        query = """
            INSERT INTO chat_responses_ (
            MODEL_, CREATED_AT_, DONE_, DONE_REASON_, TOTAL_DURATION_, LOAD_DURATION_,
            PROMPT_EVAL_COUNT_, PROMPT_EVAL_DURATION_, EVAL_COUNT_, EVAL_DURATION_, 
            MESSAGE_ROLE_, MESSAGE_CONTENT_,MESSAGE_IMAGES_, MESSAGE_TOOL_CALLS_, ROOMID_, WXID_
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s ,%s, %s, %s, %s)
        """

        # 格式化时间
        # created_at = datetime.strptime(chat["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d %H:%M:%S")
        created_at_ = chat["created_at"]
        dt = parser.isoparse(created_at_)
        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        # 数据值
        data_values = (
            chat["model"],
            formatted_time,
            chat["done"],
            chat["done_reason"],
            chat["total_duration"],
            chat["load_duration"],
            chat["prompt_eval_count"],
            chat["prompt_eval_duration"],
            chat["eval_count"],
            chat["eval_duration"],
            chat["message"]["role"],
            chat["message"]["content"],
            chat["message"].get("images"),
            chat["message"].get("tool_calls"),
            self.roomid,
            self.wxid
        )
        # 语句执行
        cursor.execute(query, data_values)
        # 清除缓存
        conn.commit()
        cursor.close()
        conn.close()

    def SaveMessages(self, role, content, table_name):
        """
        保存对话记录,作用于 messages和messages_backup 表
        """
        conn = self.GetDBConnection()
        cursor = conn.cursor()

        # 插入语句构建
        query = f"""
            INSERT INTO {table_name} (MESSAGE_ROLE_, MESSAGE_CONTENT_, WXID_, ROOMID_, CREATED_TIME_)
            VALUES (%s, %s, %s, %s, %s)
        """

        values = (role, content, self.wxid, self.roomid, datetime.now())

        # 语句执行
        cursor.execute(query, values)
        # 清除缓存
        conn.commit()
        cursor.close()
        conn.close()

    def GetMessages(self, limit=25):
        """
        构建上下文
        获取用户最近25条对话记录
        """
        conn = self.GetDBConnection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT MESSAGE_ROLE_, MESSAGE_CONTENT_
            FROM chat_messages_
            WHERE ROOMID_ = %s AND WXID_ = %s
            ORDER BY ID_ DESC
            LIMIT %s
        """
        cursor.execute(query, (self.roomid, self.wxid, limit * 2))  # 每对消息包含 user 和 assistant

        # 装载messages
        messages = cursor.fetchall()
        # 清除缓存
        cursor.close()
        conn.close()

        # 将消息按时间顺序排列
        messages.reverse()
        return messages

    def ClearContext(self):
        """
        清除用户上下文。
        """
        conn = self.GetDBConnection()
        cursor = conn.cursor()

        query = "DELETE FROM chat_messages_ WHERE ROOMID_ = %s AND WXID_ = %s"
        cursor.execute(query, (self.roomid, self.wxid))

        # 清除缓存
        conn.commit()
        cursor.close()
        conn.close()

    def iChatWithLLM(self):
        if '清除上下文' in self.userinput.strip().lower():
            self.ClearContext()
            res = '上下文已清除'
            return res

        # 获取用户历史消息
        history_messages = self.GetMessages()

        prompt = self.config.ichat["prompt"]
        # 构建messages
        messages = [{"role": "user", "content": prompt}, {"role": "assistant", "content": "好的"}]
        for msg in history_messages:
            messages.append({"role": msg["MESSAGE_ROLE_"], "content": msg["MESSAGE_CONTENT_"]})
        messages.append({"role": "user", "content": self.userinput})

        # debug
        print(messages)

        responses = ollama.chat(
            model=self.config.ichat["model"],
            messages=messages
        )

        self.SaveResponses(responses)
        self.SaveMessages("user", self.userinput, "chat_messages_")
        self.SaveMessages("assistant", responses["message"]["content"], "chat_messages_")
        self.SaveMessages("user", self.userinput, "chat_messages_backup_")
        self.SaveMessages("assistant", responses["message"]["content"], "chat_messages_backup_")

        res = responses["message"]["content"]
        return res


if __name__ == "__main__":
    wxid_test = "wxid_123457"  # 微信用户 ID
    roomid_test = "room123456"
    config_test = Config()
    # 模拟微信消息
    while True:
        # user_input = "为什么天空是蓝色的?"  # 用户输入
        usrinput = input("\nUser: ")
        if usrinput.lower() in ["exit", "quit", "stop", "baibai", "拜拜"]:
            break
        # 与 LLM 交互
        chat = ichat(config_test, wxid_test, usrinput, roomid_test)
        response = chat.iChatWithLLM()
        print("LLM 回复:", response)

