# coding: utf-8
from pathlib import Path
from .env_bootstrap import cute_box
from .constants import PRESET_KEYWORDS_2025
from . import state

from .options import RunOptions, KeywordMode, AILevel, ExtractMode

def ask_mysql_url() -> str:
    key_file = Path(__file__).with_name(".db_key")
    if key_file.exists():
        key = key_file.read_text().strip()
    else:
        key = input("请输入秘钥/キーを入力してください：user:pass@host\n>>>>>> ").strip()
        key_file.write_text(key)
    return f"mysql+pymysql://{key}:3306/na_data?charset=utf8mb4"

def wizard() -> RunOptions:
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
        "1. Lexis（当前）\n"
        "2. Factiva（未实现）",
        "【抽出モード】選択：\n"
        "1. Lexis（現在）\n"
        "2. Factiva（未実装）",
        "🗂️"
    )
    e = input("👉 输入 1/2 [Default: 1]: ").strip() or "1"
    extract_mode = ExtractMode.LEXIS if e != "2" else ExtractMode.FACTIVA
    if extract_mode == ExtractMode.FACTIVA:
        print("⚠️ Factiva 暂未实现，本次将使用 Lexis 模式运行。")
        extract_mode = ExtractMode.LEXIS

    opts = RunOptions(
        keyword_mode=keyword_mode,
        custom_keywords=custom_keys,
        ai_level=ai_level,
        extract_mode=extract_mode,
    )
    return opts

def apply_options_to_state(opts: RunOptions) -> None:
    # 关键词写入 state（你现有逻辑用 state.KEYWORD_ROOTS）
    if opts.keyword_mode == KeywordMode.CUSTOM and opts.custom_keywords:
        state.KEYWORD_ROOTS = opts.custom_keywords
    else:
        state.KEYWORD_ROOTS = PRESET_KEYWORDS_2025
