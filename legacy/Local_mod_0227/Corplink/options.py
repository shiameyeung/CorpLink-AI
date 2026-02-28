# coding: utf-8
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

class KeywordMode(str, Enum):
    PRESET_2025 = "PRESET_2025"
    CUSTOM = "CUSTOM"

class AILevel(str, Enum):
    MANUAL = "MANUAL"   # 不调用 GPT
    ASSIST = "ASSIST"   # 只生成建议，不落地写入/不执行
    AUTO = "AUTO"       # 直接跑完 Step1-4（含 GPT autofill + 入库分析）

class ExtractMode(str, Enum):
    LEXIS = "LEXIS"
    FACTIVA = "FACTIVA"

@dataclass
class RunOptions:
    keyword_mode: KeywordMode = KeywordMode.PRESET_2025
    custom_keywords: Optional[List[str]] = None
    ai_level: AILevel = AILevel.MANUAL
    extract_mode: ExtractMode = ExtractMode.LEXIS
