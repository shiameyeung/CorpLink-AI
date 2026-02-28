# coding: utf-8
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
import spacy

from .constants import NOISE_CONCEPTS, ORG_SUFFIX, TIME_QTY, FIN_REPORT
from .text_utils import _lower_ratio

nlp = spacy.load("en_core_web_sm", disable=["parser", "lemmatizer"])
model_emb = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2",
    device="cuda" if torch.cuda.is_available() else "cpu"
)

print("⏳ 正在预计算垃圾词向量...")
noise_vecs = model_emb.encode(NOISE_CONCEPTS, normalize_embeddings=True)

def calc_Bad_Score(text: str) -> int:
    score = 0
    if ORG_SUFFIX.search(text): 
        return 0

    if TIME_QTY.search(text): score += 30
    if FIN_REPORT.search(text): score += 30
    if len(text.split()) <= 2: score += 10
    if _lower_ratio(text) > 0.30: score += 10

    if score > 0 or len(text.split()) > 2:
        text_vec = model_emb.encode([text], normalize_embeddings=True)[0]
        sims = np.dot(noise_vecs, text_vec)
        max_sim = float(np.max(sims))

        if max_sim > 0.4: score += 20
        if max_sim > 0.6: score += 40
        if max_sim > 0.8: score += 100

    return score