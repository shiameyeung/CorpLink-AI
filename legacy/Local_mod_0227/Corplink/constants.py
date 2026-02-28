# coding: utf-8
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MAX_COMP_COLS = 50

STOPWORDS = {"the","and","for","with","from","that","this","have","will","are","you","not","but","all","any","one","our","their"}

PRESET_KEYWORDS_2025 = [
    'partner','alliance','collaborat','cooper','cooperat','join','merger','acquisiti',
    'outsourc','invest','licens','integrat','coordinat','synergiz','associat',
    'confedera','federa','union','unit','amalgamat','conglomerat','combin',
    'buyout','companion','concur','concert','comply','complement','assist',
    'takeover','accession','procure','suppl','conjoint','support','adjust',
    'adjunct','patronag','subsid','affiliat','endors'
]

DATE_FINDER = re.compile(
    r'\b(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+(?:Jan(?:[a-z]+)?|Feb(?:[a-z]+)?|Mar(?:[a-z]+)?|Apr(?:[a-z]+)?|May|Jun(?:[a-z]+)?|Jul(?:[a-z]+)?|Aug(?:[a-z]+)?|Sep(?:[a-z]+)?|Oct(?:[a-z]+)?|Nov(?:[a-z]+)?|Dec(?:[a-z]+)?)\s+\d{4})\b',
    re.IGNORECASE
)

ORG_SUFFIX  = re.compile(
    r'\b(Inc\.?|Corp\.?|Corporation|Ltd\.?|LLC|PLC|AG|NV|SA|GmbH|S\.p\.A|Co\.?|Company|'
    r'Group|Holdings?|Partners?|Capital|Ventures?|Bank|Trust|Software|'
    r'Technolog(?:y|ies)|Pharma(?:ceuticals)?|Systems?|Services?|'
    r'Industr(?:y|ies)|Foundation|Laborator(?:y|ies)|'
    r'University|College|Institute|School|Hospital|Center|Centre)\b',
    re.I)

TIME_QTY    = re.compile(
    r'\b(year|month|week|day|decade|centur(?:y|ies)|quarter|q[1-4]|'
    r'ago|last|next|few|couple|several|dozen|half|around|approximately)s?\b',
    re.I)

FIN_REPORT = re.compile(
    r'\b(results?|earnings?|revenues?|turnover|profit(?:s)?|loss(?:es)?|guidance|forecast|'
    r'financial statements?|balance sheets?|cash flows?|income statements?)\b',
    re.I)

ORDINAL_PERIOD = re.compile(
    r'\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\b.*?\b(quarter|half|year)\b',
    re.I)

ANNOUNCE_VERB = re.compile(
    r'\b(reports?|announces?|updates?|revises?|publishes?|files?|issues?|unveils?)\b',
    re.I)

GENERIC_NOUN = re.compile(
    r'\b(services?|solutions?|systems?|platforms?|programs?|projects?|'
    r'statements?|reports?|targets?|technologies?|operations?|activities|'
    r'strategies?|plans?)\b', re.I)

MONTH_NAME = re.compile(
    r'\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|'
    r'jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|'
    r'dec(?:ember)?)\b', re.I)

NEW_GENERIC_TIME = re.compile(
    r'\b(?:end|beginning|middle|start|first|second|third|fourth|prior|previous|'
    r'current|next)\s+(?:of\s+)?(?:the\s+)?(?:year|quarter|month|week)s?\b',
    re.I)

ALLCAP_SHORT = re.compile(r'^[A-Z]{2,4}$')
NUMERIC = re.compile(r'[%\$]\s*\d|\d[\d,\.]+\s*(?:million|billion|thousand)', re.I)
ALL_UPPER  = re.compile(r'^[A-Z]{2,}$')
ALL_LOWER  = re.compile(r'^[a-z]{4,}$')
SHORT_TOKEN = re.compile(r'^[A-Za-z]{1,4}$')
ART_LOWER   = re.compile(r'^\s*(a|an|about|approximately|the|this|that|those)\s+[a-z]')
GENERIC_END = re.compile(
    r'\b(plan|plans?|programs?|systems?|platforms?|services?|solutions?|operations?|'
    r'agreements?|strategies?|reports?|statements?)$', re.I)

NOISE_CONCEPTS = [
    "financial report results",
    "fiscal year quarter",
    "forward looking statements",
    "January February March",
    "global market growth",
    "conference call webcast",
    "operating expenses",
    "agreement partnership"
]

ANCHOR_TEXT = "Companies announce strategic partnership, joint venture, merger, acquisition, investment, or business collaboration."