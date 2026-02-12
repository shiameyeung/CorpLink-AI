# coding: utf-8
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Optional

from striprtf.striprtf import rtf_to_text

# 头部日期行：2025 12 25 21:05（中间可能有多空格）
HEAD_DATETIME = re.compile(r"\b(20\d{2})\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,2}:\d{2})\b")

# body 里常见日期：Dec. 25, 2025 /PRNewswire/ --
BODY_DATE = re.compile(
    r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|"
    r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+(\d{1,2}),\s+(20\d{2})\b",
    re.IGNORECASE,
)

@dataclass
class FactivaRecord:
    title: str
    publisher: str
    date_yyyy_mm_dd: str  # "YYYY-MM-DD" or ""
    body: str

def read_rtf_text(path: Path) -> str:
    raw = path.read_text(errors="ignore")
    txt = rtf_to_text(raw)
    # 统一换行、去掉多余空白
    txt = txt.replace("\r\n", "\n").replace("\r", "\n")
    # Factiva 有时会出现很多空行
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    return txt.strip()

def _normalize_lines(text: str) -> List[str]:
    # striprtf 之后会有很多前后空格
    lines = [ln.strip() for ln in text.split("\n")]
    # 保留空行（用于分段），但去掉连续空行可以减噪
    out: List[str] = []
    last_blank = False
    for ln in lines:
        blank = (ln == "")
        if blank and last_blank:
            continue
        out.append(ln)
        last_blank = blank
    return out

def parse_records_from_text(text: str) -> List[FactivaRecord]:
    lines = _normalize_lines(text)

    # 经验规则：一条新闻开头是一个“非空标题行”，紧跟一个“纯数字行”（字数）
    # 再往后若能在接下来的少数行里找到 HEAD_DATETIME，就认为这是一条 record 的 header
    records: List[FactivaRecord] = []

    i = 0
    n = len(lines)
    while i < n:
        title = lines[i]
        if not title:
            i += 1
            continue

        # wordcount line
        if i + 1 >= n or not re.fullmatch(r"\d{2,6}", lines[i + 1] or ""):
            i += 1
            continue

        # 在后面 10 行里找 head datetime 和 publisher
        window = "\n".join(lines[i : min(i + 12, n)])
        mdt = HEAD_DATETIME.search(window)
        if not mdt:
            i += 1
            continue

        # publisher：在 datetime 之后的下一行里通常是 publisher（如 PR Newswire）
        # 我们用“从 i 开始往后找第一个像 publisher 的非空行”作为 publisher
        pub = ""
        # 先定位 datetime 出现在第几行
        # 粗略：逐行扫描
        dt_line_idx = None
        for j in range(i, min(i + 12, n)):
            if HEAD_DATETIME.search(lines[j]):
                dt_line_idx = j
                break
        if dt_line_idx is not None:
            for j in range(dt_line_idx + 1, min(dt_line_idx + 6, n)):
                if lines[j]:
                    pub = lines[j]
                    break

        yyyy, mm, dd, _hhmm = mdt.groups()
        date_yyyy_mm_dd = f"{yyyy}-{int(mm):02d}-{int(dd):02d}"

        # body start：通常在 publisher/code/copyright 之后，遇到第一个看起来像正文的长句
        body_start = None
        for j in range(dt_line_idx + 1 if dt_line_idx is not None else i + 2, min(i + 40, n)):
            ln = lines[j]
            if not ln:
                continue
            if ln.upper().startswith("COPYRIGHT"):
                continue
            # publisher code 一般很短（如 PRN）
            if len(ln) <= 6 and ln.isupper():
                continue
            # 一般正文第一行会比较长，或者包含 “--”
            if len(ln) >= 30 or "--" in ln or " /" in ln:
                body_start = j
                break

        if body_start is None:
            i += 1
            continue

        # body end：下一个 record 的 title 位置（同样的模式：非空行 + 下一行纯数字）
        body_lines: List[str] = []
        k = body_start
        while k < n:
            # next record start?
            if lines[k] and k + 1 < n and re.fullmatch(r"\d{2,6}", lines[k + 1] or ""):
                # 但要避免正文中刚好出现这种组合（概率低），再加一个 datetime 检查
                window2 = "\n".join(lines[k : min(k + 12, n)])
                if HEAD_DATETIME.search(window2):
                    break
            body_lines.append(lines[k])
            k += 1

        body = "\n".join(body_lines).strip()
        records.append(FactivaRecord(title=title, publisher=pub, date_yyyy_mm_dd=date_yyyy_mm_dd, body=body))

        i = k
    return records