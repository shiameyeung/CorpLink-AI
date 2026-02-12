# coding: utf-8
import re
import unicodedata

def _normalize(text: str) -> str:
    t = re.sub(r"\s+", " ", text.lower().strip())
    t = re.sub(r"^[\-:\"']+|[\-:\"']+$", "", t)
    t = re.sub(r"[,.;/()]+", "", t)
    return t.strip()

def clean_text(t: str) -> str:
    return ''.join(c for c in t if unicodedata.category(c)[0] != 'C' or c in ('\n', '\t'))

def _lower_ratio(text: str) -> float:
    w = text.split()
    return sum(t[0].islower() for t in w) / len(w) if w else 0

def is_valid_token(token: str) -> bool:
    token = token.strip()
    if "@" in token or token.startswith("http"):
        return False
    if not token or all(c in "-–—・.、。！？／ー" for c in token):
        return False
    if re.search(r"\d", token) and not re.search(r"[A-Za-z]", token):
        return False
    if "  " in token:
        return False
    return True