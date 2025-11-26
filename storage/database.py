"""
爬虫数据持久化的SQLite数据库操作工具。
负责表结构初始化、连接管理、记录插入/查询/同步等。
所有关键函数和字段均有详细注释。
"""
from __future__ import annotations  # 兼容未来类型注解语法

import json
import glob
from datetime import datetime

import sqlite3  # 标准库SQLite操作
from contextlib import contextmanager  # 上下文管理器，简化连接关闭
from pathlib import Path  # 路径处理
from typing import Generator, Iterable, Optional  # 类型注解

from storage.config import DATABASE_PATH  # 数据库文件路径配置

# 数据库表结构定义，包含爬取记录所有字段
SCHEMA = """
CREATE TABLE IF NOT EXISTS crawled_records (
    id TEXT PRIMARY KEY,              -- 唯一ID
    title TEXT NOT NULL,              -- 标题
    url TEXT NOT NULL,                -- 详情页链接
    publish_time TEXT,                -- 发布时间
    source_id TEXT,                   -- 来源ID
    source_name TEXT,                 -- 来源名称
    attachments TEXT,                 -- 附件JSON
    content TEXT,                     -- 详情页内容
    created_at TEXT DEFAULT CURRENT_TIMESTAMP -- 创建时间
);
CREATE INDEX IF NOT EXISTS idx_crawled_records_url ON crawled_records(url); -- 加速URL查询
"""

def query_records(source_ids: list, start_time: str, end_time: str) -> list:
    """
    查询指定 source_ids（列表）相关的所有记录，时间范围为 start_time 到 end_time。
    自动查找 config 目录下所有 json 文件，加载 sources 列表中的所有 id。
    返回结果为 JSON 格式的列表。
    """
    # 1. 查找 config 目录下所有 json 文件，收集所有 sources 的 id
    config_files = []
    for src in source_ids:
        config_files.extend(glob.glob(f"config/sources/{src}.json"))
    all_ids = []
    for file in config_files:
        try:
            with open(file, encoding="utf-8") as f:
                data = json.load(f)
            for src in data.get("sources", []):
                sid = src.get("id")
                if sid:
                    all_ids.append(sid)
        except Exception:
            continue
    if not all_ids:
        return []
    # 3. 查询数据库
    results = []
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.execute(
            f"""
            SELECT id, title, url, publish_time, source_id, source_name, attachments, content, created_at
            FROM crawled_records
            WHERE source_id IN ({','.join(['?']*len(all_ids))})
              AND publish_time >= ? AND publish_time <= ?
            ORDER BY publish_time DESC
            """,
            (*all_ids, start_time, end_time)
        )
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
    return results

def initialize() -> None:
    """
    初始化数据库文件和表结构，确保可用。
    若目录不存在则自动创建。
    """
    path = Path(DATABASE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)

def record_exists(record_id: str) -> bool:
    """
    判断指定ID的记录是否已存在。
    用于去重，避免重复入库。
    """
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.execute("SELECT 1 FROM crawled_records WHERE id=?", (record_id,))
        return cursor.fetchone() is not None

def store_document(item_id: str, content: str, metadata: dict) -> None:
    """
    存储文档内容及元数据到本地SQLite。
    item_id: 唯一ID
    content: 详情页内容
    metadata: 需包含 title, url, publish_time, source_id, source_name, attachments (JSON字符串)
    """
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO crawled_records
            (id, title, url, publish_time, source_id, source_name, attachments, content)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                metadata.get("title", ""),
                metadata.get("url", ""),
                metadata.get("publish_time"),
                metadata.get("source_id", ""),
                metadata.get("source_name", ""),
                metadata.get("attachments"),
                content,
            ),
        )
        conn.commit()
