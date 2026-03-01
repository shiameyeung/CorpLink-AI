# coding: utf-8
import json
import os

def load_web_config():
    """
    尝试从当前运行目录（沙盒目录）读取 config.json。
    如果文件不存在，则返回一个空字典，后续代码会使用默认值。
    """
    config_path = os.path.join(os.getcwd(), "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# 导出一个全局变量，供其他模块调用
WEB_CONFIG = load_web_config()

from pathlib import Path

from .env_bootstrap import cute_box
from .constants import PRESET_KEYWORDS_2025, BASE_DIR
from . import state
from .options import RunOptions, KeywordMode, AILevel, ExtractMode

def ask_mysql_url() -> str:
    # 优先读取前端传来的数据库地址，如果没有，则使用你写死的默认地址
    default_url = "mysql+pymysql://webapp:vE8#kZ9$nQ2!mP5@@127.0.0.1:3306/CorpLink?charset=utf8mb4"
    return WEB_CONFIG.get("mysql_url", default_url)

def wizard() -> RunOptions:
    # ====== 新增：Web 模式检测 ======
    # 如果读取到了 config.json (WEB_CONFIG有内容)，则自动跳过所有 input()
    if WEB_CONFIG:
        print("🌐 检测到 Web 环境配置，自动读取参数，跳过手动输入...")
        
        km = str(WEB_CONFIG.get("keyword_mode", "1"))
        if km == "2":
            keyword_mode = KeywordMode.CUSTOM
            custom_keys = WEB_CONFIG.get("custom_keywords", [])
        else:
            keyword_mode = KeywordMode.PRESET_2025
            custom_keys = None
            
        a = str(WEB_CONFIG.get("ai_level", "3")) # 默认 3 全自动
        ai_level = {"1": AILevel.MANUAL, "2": AILevel.ASSIST, "3": AILevel.AUTO}.get(a, AILevel.AUTO)
        
        e = str(WEB_CONFIG.get("extract_mode", "2")) # 默认 2 FACTIVA
        extract_mode = ExtractMode.LEXIS if e != "2" else ExtractMode.FACTIVA
        
        return RunOptions(
            keyword_mode=keyword_mode,
            custom_keywords=custom_keys,
            ai_level=ai_level,
            extract_mode=extract_mode,
        )

    # ====== 终端模式：保持原有的手动输入逻辑 ======
    # 1) Keyword
    cute_box(
        "【参数配置】请选择关键词模式：\n"
        "1. 2025 AI x Healthcare (默认)\n"
        "2. 自定义关键词（逗号分隔）",
        "【設定】キーワードモードを選択してください：\n"
        "1. 2025 AI x Healthcare (デフォルト)\n"
        "2. カスタム（カンマ区切り）",
        "🧩"
    )
    km = input("👉 输入 1/2 [Default: 1]: ").strip() or "1"
    if km == "2":
        raw = input("👉 请输入自定义关键词（逗号分隔）/ カスタムキーワード: ").strip()
        custom_keys = [k.strip().strip("'").strip('"') for k in raw.replace("，", ",").split(",") if k.strip()]
        if not custom_keys:
            print("❌ 格式错误，回退到默认关键词集")
            keyword_mode = KeywordMode.PRESET_2025
            custom_keys = None
        else:
            keyword_mode = KeywordMode.CUSTOM
    else:
        keyword_mode = KeywordMode.PRESET_2025
        custom_keys = None

    # 2) AI level
    cute_box(
        "【AI 使用程度】请选择：\n"
        "1. 全手动：不使用 AI（不生成建议列）\n"
        "2. 参考：使用 AI 生成建议（写入新列，不覆盖 Canonical_Name）\n"
        "3. 全自动：全流程自动执行（Step 1-4）",
        "【AI】選択してください：\n"
        "1. 手動：AIを使わない\n"
        "2. 参考：AIで提案列を生成（新規列に保存）\n"
        "3. 自動：全自動実行（Step 1-4）",
        "🤖"
    )
    a = input("👉 输入 1/2/3 [Default: 1]: ").strip() or "1"
    ai_level = {"1": AILevel.MANUAL, "2": AILevel.ASSIST, "3": AILevel.AUTO}.get(a, AILevel.MANUAL)

    # 3) Extract mode
    cute_box(
        "【抽取模式】请选择：\n"
        "1. Lexis（docx）\n"
        "2. Factiva（rtf）",
        "【抽出モード】選択：\n"
        "1. Lexis（docx）\n"
        "2. Factiva（rtf）",
        "🗂️"
    )
    e = input("👉 输入 1/2 [Default: 1]: ").strip() or "1"
    extract_mode = ExtractMode.LEXIS if e != "2" else ExtractMode.FACTIVA

    return RunOptions(
        keyword_mode=keyword_mode,
        custom_keywords=custom_keys,
        ai_level=ai_level,
        extract_mode=extract_mode,
    )

def apply_options_to_state(opts: RunOptions) -> None:
    # Keywords
    if opts.keyword_mode == KeywordMode.CUSTOM and opts.custom_keywords:
        state.KEYWORD_ROOTS = opts.custom_keywords
    else:
        state.KEYWORD_ROOTS = PRESET_KEYWORDS_2025

    # Extract mode (必修 4 需要它)
    state.EXTRACT_MODE = opts.extract_mode.value

# ====== 旧接口保留（兼容），但建议主流程不用 ======
def configure_keywords():
    # 兼容旧调用：默认直接写 preset
    state.KEYWORD_ROOTS = PRESET_KEYWORDS_2025

def choose() -> str:
    # 兼容旧菜单：直接返回 "0" 等不再使用
    return "0"
