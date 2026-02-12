# coding: utf-8
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

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


def _clean_line(ln: str) -> str:
    # 去掉不可见字符与全角空格
    return ln.replace("\u00a0", " ").replace("\u200b", "").strip()


def _normalize_lines(text: str) -> List[str]:
    lines = [_clean_line(ln) for ln in text.split("\n")]
    out: List[str] = []
    last_blank = False
    for ln in lines:
        blank = (ln == "")
        if blank and last_blank:
            continue
        out.append(ln)
        last_blank = blank
    return out


def _parse_head_datetime_from_lines(lines: List[str]) -> Tuple[str, Optional[int]]:
    """
    兼容两种头部日期：
    1) 单行：2025 12 25 21:05
    2) 多行拆分（含 年/月/日 分隔）
    """
    # 1) 单行形式
    for idx, ln in enumerate(lines):
        m = HEAD_DATETIME.search(ln)
        if m:
            yyyy, mm, dd, _hhmm = m.groups()
            return f"{yyyy}-{int(mm):02d}-{int(dd):02d}", idx

    # 2) 多行拆分形式：收集数字 token
    tokens: List[Tuple[int, str]] = []
    for idx, ln in enumerate(lines):
        for tok in re.findall(r"\d{1,4}(?::\d{2})?", ln):
            tokens.append((idx, tok))

    for i, (line_idx, tok) in enumerate(tokens):
        if re.fullmatch(r"20\d{2}", tok):
            if i + 3 < len(tokens):
                mm = tokens[i + 1][1]
                dd = tokens[i + 2][1]
                hhmm = tokens[i + 3][1]
                if (re.fullmatch(r"\d{1,2}", mm)
                        and re.fullmatch(r"\d{1,2}", dd)
                        and re.fullmatch(r"\d{1,2}:\d{2}", hhmm)):
                    yyyy = int(tok)
                    return f"{yyyy:04d}-{int(mm):02d}-{int(dd):02d}", tokens[i + 3][0]
    return "", None


def parse_records_from_text(text: str) -> List[FactivaRecord]:
    lines = _normalize_lines(text)
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

        window = lines[i: min(i + 18, n)]
        date_yyyy_mm_dd, dt_rel_idx = _parse_head_datetime_from_lines(window)
        if not date_yyyy_mm_dd:
            i += 1
            continue

        dt_line_idx = i + (dt_rel_idx if dt_rel_idx is not None else 0)

        # publisher：在 datetime 之后的下一行里通常是 publisher
        pub = ""
        for j in range(dt_line_idx + 1, min(dt_line_idx + 6, n)):
            if lines[j]:
                # 跳过纯短代码行
                if len(lines[j]) <= 6 and lines[j].isupper():
                    continue
                pub = lines[j]
                break

        # body start
        body_start = None
        for j in range(dt_line_idx + 1, min(i + 50, n)):
            ln = lines[j]
            if not ln:
                continue
            if ln.upper().startswith("COPYRIGHT"):
                continue
            if len(ln) <= 6 and ln.isupper():
                continue
            if len(ln) >= 30 or "--" in ln or " /" in ln:
                body_start = j
                break

        if body_start is None:
            i += 1
            continue

        # body end
        body_lines: List[str] = []
        k = body_start
        while k < n:
            if lines[k] and k + 1 < n and re.fullmatch(r"\d{2,6}", lines[k + 1] or ""):
                window2 = "\n".join(lines[k: min(k + 12, n)])
                if HEAD_DATETIME.search(window2) or _parse_head_datetime_from_lines(lines[k: min(k + 12, n)])[0]:
                    break
            body_lines.append(lines[k])
            k += 1

        body = "\n".join(body_lines).strip()
        records.append(FactivaRecord(title=title, publisher=pub, date_yyyy_mm_dd=date_yyyy_mm_dd, body=body))

        i = k

    return records
