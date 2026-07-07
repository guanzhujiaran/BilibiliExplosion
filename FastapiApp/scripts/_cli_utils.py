# -*- coding: utf-8 -*-
"""
脚本通用 CLI 工具：大模型 & 数据库参数注入。

backfill_dyninfo_from_rawjson / judge_grand_prize 共用。
"""
import argparse


def add_llm_args(parser: argparse.ArgumentParser) -> None:
    """向 ArgumentParser 添加大模型参数组"""
    g = parser.add_argument_group("大模型配置 (覆盖 .env 默认值)")
    g.add_argument("--llm-base-url", type=str, default=None, help="LLM API base URL")
    g.add_argument("--llm-token", type=str, default=None, help="LLM API token / key")
    g.add_argument("--llm-model", type=str, default=None, help="模型名称，如 gpt-4o / qwen3.5")


def add_db_args(parser: argparse.ArgumentParser) -> None:
    """向 ArgumentParser 添加数据库参数组"""
    g = parser.add_argument_group("目标数据库配置 (覆盖 .env 默认值)")
    g.add_argument("--db-host", type=str, default=None, help="MySQL 主机")
    g.add_argument("--db-port", type=str, default=None, help="MySQL 端口")
    g.add_argument("--db-user", type=str, default=None, help="MySQL 用户名")
    g.add_argument("--db-password", type=str, default=None, help="MySQL 密码")


def apply_cli_overrides(args: argparse.Namespace) -> None:
    """将命令行参数注入 CONFIG / Settings，覆盖 .env 默认值"""
    from CONFIG import settings, CONFIG, DataBaseConfig, LLMApiConfig

    # ---- 大模型配置 ----
    llm_overrides: dict[str, str] = {}
    if args.llm_base_url:
        llm_overrides["base_url"] = args.llm_base_url
    if args.llm_token:
        llm_overrides["token"] = args.llm_token
    if args.llm_model:
        llm_overrides["model_name"] = args.llm_model

    if llm_overrides:
        llm_overrides.setdefault("base_url", "http://localhost:11434/v1")
        llm_overrides.setdefault("token", "ollama")
        llm_overrides.setdefault("model_name", "qwen3.5")
        settings.llm_apis = [LLMApiConfig(**llm_overrides)]
        print(f"[CLI] LLM 覆盖: {llm_overrides['base_url']} / {llm_overrides['model_name']}")

    # ---- 数据库配置 ----
    need_rebuild = any([
        args.db_host, args.db_port, args.db_user, args.db_password,
    ])

    if need_rebuild:
        if args.db_host:
            settings.MYSQL_HOST = args.db_host
        if args.db_port:
            settings.MYSQL_PORT = args.db_port
        if args.db_user:
            settings.MYSQL_USER = args.db_user
        if args.db_password:
            settings.MYSQL_PASSWORD = args.db_password
        CONFIG.database.MYSQL = DataBaseConfig._MYSQL()
        print(f"[CLI] DB 覆盖: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")
