# coding: utf-8
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from striprtf.striprtf import rtf_to_text

HEAD_DATETIME = re.compile(r"\b(20\d{2})\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,2}:\d{2})\b")
DATE_JP = re.compile(r"(20\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日\s*(\d{1,2}:\d{2})")
DATE_SLASH = re.compile(r"(20\d{2})[/-](\d{1,2})[/-](\d{1,2})\s+(\d{1,2}:\d{2})")

BODY_DATE = re.compile(
    r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|"
    r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+(\d{1,2}),\s+(20\d{2})\b",
    re.IGNORECASE,
)

WORDCOUNT = re.compile(r"[\d,]+\s*(語|words?)?$", re.I)
DOC_ID = re.compile(r"^(文書|documents?)\b", re.I)
LANG_LINE = re.compile(r"^(英語|日本語|中文|Chinese|English|Japanese)$", re.I)

@dataclass
class FactivaRecord:
    title: str
    publisher: str
    date_yyyy_mm_dd: str
    body: str


def read_rtf_text(path: Path) -> str:
    raw = path.read_text(errors="ignore")
    txt = rtf_to_text(raw)
    txt = txt.replace("\r\n", "\n").replace("\r", "\n")
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    return txt.strip()


def _clean_line(ln: str) -> str:
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


def _find_header_date(lines: List[str]) -> Tuple[str, Optional[int]]:
    for idx, ln in enumerate(lines):
        m = DATE_JP.search(ln)
        if m:
            yyyy, mm, dd, _hhmm = m.groups()
            return f"{yyyy}-{int(mm):02d}-{int(dd):02d}", idx
        m = DATE_SLASH.search(ln)
        if m:
            yyyy, mm, dd, _hhmm = m.groups()
            return f"{yyyy}-{int(mm):02d}-{int(dd):02d}", idx

    for idx, ln in enumerate(lines):
        m = HEAD_DATETIME.search(ln)
        if m:
            yyyy, mm, dd, _hhmm = m.groups()
            return f"{yyyy}-{int(mm):02d}-{int(dd):02d}", idx

    tokens: List[Tuple[int, str]] = []
    for idx, ln in enumerate(lines):
        for tok in re.findall(r"\d{1,4}(?::\d{2})?", ln):
            tokens.append((idx, tok))

    for i, (_, tok) in enumerate(tokens):
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


def _find_wordcount(lines: List[str], start: int, max_ahead: int = 10) -> Optional[int]:
    for j in range(start, min(start + max_ahead, len(lines))):
        if WORDCOUNT.fullmatch(lines[j] or ""):
            return j
    return None


def _split_chunks(lines: List[str]) -> List[List[str]]:
    chunks: List[List[str]] = []
    buf: List[str] = []
    for ln in lines:
        if re.search(r"\(END\)", ln):
            if buf:
                chunks.append(buf)
                buf = []
            continue
        if DOC_ID.match(ln) and buf:
            chunks.append(buf)
            buf = [ln]
            continue
        buf.append(ln)
    if buf:
        chunks.append(buf)
    return chunks


def _find_title_index(lines: List[str]) -> Optional[int]:
    for idx, ln in enumerate(lines):
        if not ln:
            continue
        if DOC_ID.match(ln):
            continue
        if LANG_LINE.match(ln):
            continue
        if WORDCOUNT.fullmatch(ln):
            continue
        if ln.upper().startswith("COPYRIGHT"):
            continue
        if _find_wordcount(lines, idx + 1, max_ahead=6) is not None:
            return idx
        if _find_header_date(lines[idx: idx + 12])[0]:
            return idx
    return None


def _parse_record_from_chunk(lines: List[str]) -> Optional[FactivaRecord]:
    lines = [ln for ln in lines if ln.strip()]
    if not lines:
        return None

    title_idx = _find_title_index(lines)
    if title_idx is None:
        return None
    title = lines[title_idx]

    date_yyyy_mm_dd, dt_idx = _find_header_date(lines[title_idx: min(title_idx + 40, len(lines))])
    if dt_idx is not None:
        dt_idx = title_idx + dt_idx

    pub = ""
    if dt_idx is not None:
        for j in range(dt_idx + 1, min(dt_idx + 12, len(lines))):
            if not lines[j]:
                continue
            if WORDCOUNT.fullmatch(lines[j] or ""):
                continue
            if len(lines[j]) <= 6 and lines[j].isupper():
                continue
            if LANG_LINE.match(lines[j]):
                continue
            pub = lines[j]
            break

    body_start = None
    start_scan = (dt_idx + 1) if dt_idx is not None else title_idx + 1
    for j in range(start_scan, len(lines)):
        ln = lines[j]
        if ln.upper().startswith("COPYRIGHT"):
            continue
        if len(ln) <= 6 and ln.isupper():
            continue
        if LANG_LINE.match(ln):
            continue
        if len(ln) >= 30 or "--" in ln or " /" in ln:
            body_start = j
            break

    if body_start is None:
        return None

    body = "\n".join(lines[body_start:]).strip()
    return FactivaRecord(title=title, publisher=pub, date_yyyy_mm_dd=date_yyyy_mm_dd, body=body)


def parse_records_from_text(text: str) -> List[FactivaRecord]:
    lines = _normalize_lines(text)
    records: List[FactivaRecord] = []

    chunks = _split_chunks(lines)
    for chunk in chunks:
        rec = _parse_record_from_chunk(chunk)
        if rec and rec.body:
            records.append(rec)

    return records
