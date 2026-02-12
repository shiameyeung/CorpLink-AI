# coding: utf-8
import re
from typing import List, Dict, Set

import pandas as pd
from sqlalchemy import create_engine, text
from tqdm import tqdm
import numpy as np
from rapidfuzz import fuzz, process

from .env_bootstrap import cute_box
from .constants import BASE_DIR, MAX_COMP_COLS
from . import state
from .model_utils import nlp, model_emb, calc_Bad_Score
from .text_utils import is_valid_token

def dedup_company_cols(df: pd.DataFrame) -> pd.DataFrame:
    comp_cols = [c for c in df.columns if c.startswith("company_")]
    for ridx in df.index:
        seen: Set[str] = set()
        for col in comp_cols:
            val = str(df.at[ridx, col]).strip()
            if val in seen:
                df.at[ridx, col] = ""
            else:
                seen.add(val)
    return df

def extract_companies(text: str,
                      company_db: List[str],
                      ner_model,
                      fuzzy_threshold: int = 95) -> List[str]:
    comps: Set[str] = set()

    text_clean = re.sub(r"\s*\d{1,2}/\d{1,2}/\d{2,4}.*$", "", text).strip()
    text_clean = re.sub(r"[®™©]", "", text_clean)
    text_clean = re.sub(r"\(\s*[A-Z]{1,3}\s*\)", "", text_clean)
    text_clean = re.sub(r"\b\S+@\S+\b", "", text_clean)

    doc = ner_model(text_clean)
    for ent in doc.ents:
        ent_text = ent.text.strip()

        if "  " in ent_text or re.search(r"[\d/%+]|[^\x00-\x7F]", ent_text):
            continue
        valid_ent = True
        for w in ent_text.split():
            if (not w[0].isalpha()
                or w in {"The","And","For","With","From","That","This"}
                or not is_valid_token(w)):
                valid_ent = False
                break
        if valid_ent:
            comps.add(ent_text)

    for m in re.findall(r"\b([A-Z]{2,})ers\b", text_clean):
        comps.add(m)

    STOPWORDS = {"The","And","For","With","From","That","This","Have","Will",
                "Are","You","Not","But","All","Any","One","Our","Their"}

    tokens = re.findall(r"\b\S+\b", text_clean)
    for pos, token in enumerate(tokens):
        if (pos == 0 or token in STOPWORDS
            or any(ch in token for ch in "/%+") or "  " in token
            or len(token) < 5 or not token[0].isupper() or token.isupper()
            or re.search(r"\d|[^\x00-\x7F]", token)
            or not is_valid_token(token)):
            continue

        if any(token.lower() == db.lower() for db in company_db):
            comps.add(token)

    return list(comps)

def step2(mysql_url: str):
    cute_box(
        "Step-2：公司识别＋BAN 过滤 中…",
        "Step-2：企業名認識＋BAN フィルタ中…",
        "🏷️"
    )
    engine_tmp = create_engine(mysql_url)
    df_canon = pd.read_sql("SELECT id, canonical_name FROM company_canonical", engine_tmp)
    df_canon.to_csv(BASE_DIR / "canonical_list.csv", index=False, encoding="utf-8-sig")
    cute_box(
        f"已写出 canonical_list.csv，共 {len(df_canon)} 行",
        f"canonical_list.csv を保存しました：{len(df_canon)} 行",
        "🗂️"
    )

    engine = create_engine(mysql_url)
    with engine.begin() as conn:
        ban_set = {r[0] for r in conn.execute(text("SELECT alias FROM ban_list"))}
        rows = conn.execute(text("""
            SELECT a.alias, c.canonical_name FROM company_alias a
            JOIN company_canonical c ON a.canonical_id = c.id
        """))
        alias_map = {alias: canon for alias, canon in rows}
        canon_set = {r[0] for r in conn.execute(text("SELECT canonical_name FROM company_canonical"))}
        canon_names = list(canon_set)
        canon_vecs  = model_emb.encode(canon_names, batch_size=64, normalize_embeddings=True)
        rows2 = conn.execute(text(
            "SELECT id, canonical_name FROM company_canonical"
        ))
        canon_name2id = {name: cid for cid, name in rows2}
    
    cute_box(
    f"ban_list={len(ban_set)}，alias_map={len(alias_map)}，canon_set={len(canon_set)}",
    f"ban_list：{len(ban_set)}件／alias_map：{len(alias_map)}件／canon_set：{len(canon_set)}件",
    "🔍"
    )

    df = pd.DataFrame(state.SENTENCE_RECORDS)
    df_hit = df[df["Hit_Count"].astype(int) >= 1].reset_index(drop=True)
    if df_hit.empty:
        cute_box(
        "Step-1 没提取到任何句子，请先跑 Step-1！",
        "Step-1 で文が取得できませんでした。まず Step-1 を実行してね",
        "🚫"
        )
        return

    company_db = list(canon_set) + list(alias_map.keys())
    comp_cols: List[List[str]] = []
    for sent in tqdm(df_hit["Sentence"].tolist(), desc="公司识别"):
        names_raw = extract_companies(sent, company_db, nlp)
        uniq: List[str] = []
        for alias in names_raw:
            if alias in uniq:     
                continue
            uniq.append(alias)
        comp_cols.append(uniq[:MAX_COMP_COLS])

    for i in range(MAX_COMP_COLS):
        df_hit[f"company_{i+1}"] = [lst[i] if i < len(lst) else "" for lst in comp_cols]
        
    ban_lower     = {b.lower() for b in ban_set}
    canon_lower   = {c.lower() for c in canon_set}
    alias_lower   = {a.lower(): canon for a, canon in alias_map.items()}
    canon_lower2orig = {c.lower(): c for c in canon_set}

    def _norm_key(s: str) -> str:
        return re.sub(r"[^A-Za-z0-9]", "", s).lower()

    comp_cols = [f"company_{i+1}" for i in range(MAX_COMP_COLS)]

    for ridx in df_hit.index:
        orig_names = [df_hit.at[ridx, c].strip() for c in comp_cols if df_hit.at[ridx, c].strip()]
        new_names  = []
        for nm in orig_names:
            nm_l = nm.lower()
            if nm_l in ban_lower:
                continue
            if nm_l in canon_lower:
                new_names.append(canon_lower2orig[nm_l])
                continue
            if nm_l in alias_lower:
                new_names.append(alias_lower[nm_l])
                continue
            new_names.append(nm)

        cleaned = []
        seen_keys = set()
        for nm in sorted(new_names, key=len, reverse=True):
            key = _norm_key(nm)
            if any(key in k or k in key for k in seen_keys):
                continue
            cleaned.append(nm)
            seen_keys.add(key)
        for i, col in enumerate(comp_cols):
            df_hit.at[ridx, col] = cleaned[i] if i < len(cleaned) else ""

    meta_cols = ["Tier_1", "Tier_2", "Filename", "Date",
                 "Title", "Publisher", "Sentence",
                 "Hit_Count", "Matched_Keywords"]

    df_final = (df_hit[meta_cols +
                [c for c in df_hit.columns if c.startswith("company_")]]
                .fillna(""))
    df_final = dedup_company_cols(df_final)

    df_final.to_csv(BASE_DIR / "result.csv",
                    index=False, encoding="utf-8-sig")
    cute_box(
        f"已生成 result.csv，共 {len(df_final)} 条记录",
        f"result.csv を生成しました：全{len(df_final)}件",
        "📑"
    )

    canon_name2id = {row.canonical_name: row.id for row in df_canon.itertuples()}

    todo_rows: List[Dict] = []
    ban_hits = alias_hits = canon_hits = 0
    rows_skipped_not_enough_companies = 0

    comp_cols = [c for c in df_final.columns if c.startswith("company_")]

    for _, row in df_final.iterrows():
        names = [row[c].strip() for c in comp_cols if row[c].strip()]

        unknowns: List[str] = []
        for alias in names:
            alias_l = alias.lower()
            if alias_l in ban_lower:
                ban_hits += 1
                continue
            if alias_l in alias_lower:
                alias_hits += 1
                continue
            if alias_l in canon_lower:
                canon_hits += 1
                continue
            unknowns.append(alias)

        if len(names) < 2:
            rows_skipped_not_enough_companies += 1
            continue

        if len(canon_vecs) > 0 and unknowns:
            unknown_vecs = model_emb.encode(unknowns, normalize_embeddings=True)
        else:
            unknown_vecs = []

        for i, alias in enumerate(unknowns):
            advice = ""
            adviced_id = ""
            match_info = ""
            
            fuzzy_res = process.extractOne(alias, canon_names, scorer=fuzz.token_sort_ratio)
            
            if fuzzy_res:
                candidate, score, _ = fuzzy_res
                if score >= 90:
                    advice = candidate
                    adviced_id = canon_name2id.get(advice, "")
                    match_info = f"Fuzzy({score:.0f})"
            
            if not advice and len(canon_vecs) > 0:
                curr_vec = unknown_vecs[i]
                sims = np.dot(canon_vecs, curr_vec)
                best_idx = int(np.argmax(sims))
                vector_score = float(sims[best_idx])
                
                if vector_score >= 0.82:
                    advice = canon_names[best_idx]
                    adviced_id = canon_name2id.get(advice, "")
                    match_info = f"AI({vector_score:.2f})"

            todo_rows.append({
                "Sentence": row["Sentence"],
                "Alias":    alias,
                "Bad_Score": calc_Bad_Score(alias),
                "Advice":   advice,
                "Adviced_ID": adviced_id,
                "Canonical_Name": "",
                "Std_Result": ""
            })

    todo_cols = [
        "Sentence", "Alias", "Bad_Score",
        "Advice", "Adviced_ID",
        "Canonical_Name", "Std_Result"
    ]

    if not todo_rows:
        todo_df = pd.DataFrame(columns=todo_cols)
        todo_df.to_csv(BASE_DIR / "result_mapping_todo.csv",
                       index=False, encoding="utf-8-sig")

        cute_box(
            "本批没有产生新的别名需要映射；已被规则识别/过滤，或因“同行公司不足（<2）”规则而跳过。\n"
            f"（ban 命中：{ban_hits}，已有 alias：{alias_hits}，已有 canonical：{canon_hits}，同行公司不足跳过：{rows_skipped_not_enough_companies}）",
            "今回のバッチでは新しい別名はありません。既存データに一致／除外、または「同一行の企業数が2未満」規則でスキップされました。\n"
            f"ban 一致：{ban_hits}／既存エイリアス：{alias_hits}／既存カノニカル：{canon_hits}／同一行の企業数不足スキップ：{rows_skipped_not_enough_companies}",
            "ℹ️"
        )
    else:
        todo_df = pd.DataFrame(todo_rows)
        todo_df["__alias_l"] = todo_df["Alias"].str.lower()
        todo_df = todo_df.drop_duplicates("__alias_l").drop(columns="__alias_l")

        todo_df["__grp"] = todo_df["Bad_Score"].apply(lambda x: 0 if x >= 50 else (1 if x >= 10 else 2))
        todo_df = (todo_df
                   .sort_values(["__grp", "Sentence"], ascending=[True, True])
                   .drop(columns="__grp"))

        for col in todo_cols:
            if col not in todo_df.columns:
                todo_df[col] = ""
        todo_df = todo_df[todo_cols]

        todo_df["Bad_Score"] = todo_df["Bad_Score"].astype(int).astype(str)
        todo_df['Sentence'] = todo_df['Sentence'].apply(
            lambda s: "'" + s if isinstance(s, str) and s.startswith('=') else s
        )
        todo_df.to_csv(BASE_DIR / "result_mapping_todo.csv",
                       index=False, encoding="utf-8-sig")

        cute_box(
            f"已生成 result_mapping_todo.csv，共 {len(todo_df)} 条待处理别名。\n"
            f"（ban 命中：{ban_hits}，已有 alias：{alias_hits}，已有 canonical：{canon_hits}，同行公司不足跳过：{rows_skipped_not_enough_companies}）",
            f"result_mapping_todo.csv を作成：{len(todo_df)} 件の候補。\n"
            f"（ban 一致：{ban_hits}／既存エイリアス：{alias_hits}／既存カノニカル：{canon_hits}／同一行の企業数不足スキップ：{rows_skipped_not_enough_companies}）",
            "📝"
        )
        
    cute_box(
    "Step-2 完成！请编辑 result_mapping_todo.csv 然后运行 Step-3",
    "Step-2 完了！result_mapping_todo.csv を編集してから Step-3 を実行してね",
    "✅"
    )
    cute_box(
        "result_mapping_todo.csv 快速填写指南：\n"
        "1) 空白→跳过\n"
        "2) 0→加 ban_list\n"
        "3) n→视为 canonical_id\n"
        "4) 其他→新/已有标准名",
        "result_mapping_todo.csv 簡易入力ガイド：\n"
        "1) ブランク→スキップ\n"
        "2) 0→ban_list登録\n"
        "3) n→canonical_id と見なす\n"
        "4) その他→新規/既存標準名",
        "📋"
    )