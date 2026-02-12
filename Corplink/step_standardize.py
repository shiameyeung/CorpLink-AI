# coding: utf-8
import random
from datetime import datetime
import re
import pandas as pd
from sqlalchemy import create_engine, text

from .env_bootstrap import cute_box
from .constants import BASE_DIR
from .step_company import dedup_company_cols

def step3(mysql_url: str):
    process_id = datetime.now().strftime("%Y%m%d") + f"{random.randint(0, 99999999):08d}"
    res_f  = BASE_DIR / "result.csv"
    todo_f = BASE_DIR / "result_mapping_todo.csv"
    if not (res_f.exists() and todo_f.exists()):
        cute_box(
            "找不到 result.csv 或 result_mapping_todo.csv，请先生成它们",
            "result.csv または result_mapping_todo.csv が見つかりません。先に作成してね",
            "❗"
        )
        return

    df_res = pd.read_csv(res_f,  dtype=str).fillna("")
    df_map = pd.read_csv(todo_f, dtype=str).fillna("")
    if "Process_ID" not in df_map.columns:
        df_map["Process_ID"] = ""

    engine = create_engine(mysql_url)
    with engine.begin() as conn:
        ban_set    = {r[0] for r in conn.execute(text("SELECT alias FROM ban_list"))}
        canon_map  = {r[0]: r[1] for r in conn.execute(text("SELECT id, canonical_name FROM company_canonical"))}
        alias_map  = {r[0]: r[1] for r in conn.execute(text(
            "SELECT a.alias, c.canonical_name FROM company_alias a "
            "JOIN company_canonical c ON a.canonical_id=c.id"
        ))}
        ban_lower       = {b.lower() for b in ban_set}
        alias_lower_map = {a.lower(): c for a, c in alias_map.items()}
        canon_lower2id  = {name.lower(): cid for cid, name in canon_map.items()}

    for idx, row in df_map.iterrows():
        alias_raw   = row["Alias"].strip()
        alias_raw_l = alias_raw.lower()
        canon_input = row["Canonical_Name"].strip()
        if not canon_input:
            df_map.at[idx, "Std_Result"] = "No input"
            continue

        if canon_input == "0":
            if alias_raw_l not in ban_lower:
                try:
                    with engine.begin() as conn:
                        conn.execute(text(
                            "INSERT IGNORE INTO ban_list(alias, process_id) VALUES (:a, :pid)"
                        ), {"a": alias_raw, "pid": process_id})
                    ban_lower.add(alias_raw_l)
                except Exception as e:
                    print(f"⚠️ Ban insert skip: {e}")
            df_map.at[idx, "Std_Result"]   = "Banned"
            df_map.at[idx, "Process_ID"] = f"'{process_id}"
            continue

        if canon_input.isdigit():
            cid = int(canon_input)
            if cid not in canon_map:
                df_map.at[idx, "Std_Result"] = "Bad ID"
                continue
            canon_name = canon_map[cid]
        else:
            ci_l = canon_input.lower()
            if ci_l not in canon_lower2id:
                try:
                    with engine.begin() as conn:
                        res = conn.execute(text(
                            "INSERT INTO company_canonical(canonical_name, process_id) VALUES (:c, :pid)"
                        ), {"c": canon_input, "pid": process_id})
                    new_id = res.lastrowid
                except Exception as e:
                    print(f"⚠️ 发现潜在重复公司: {canon_input}，尝试从数据库获取 ID...")
                    with engine.begin() as conn:
                        rows = conn.execute(text(
                            "SELECT id FROM company_canonical WHERE canonical_name = :c"
                        ), {"c": canon_input}).fetchall()
                        
                        if rows:
                            new_id = rows[0][0]
                            print(f"   -> 已找回现有 ID: {new_id}")
                        else:
                            print(f"❌ 无法解决的冲突，跳过此条: {e}")
                            df_map.at[idx, "Std_Result"] = "DB Error"
                            continue

                canon_map[new_id]        = canon_input
                canon_lower2id[ci_l]     = new_id
                df_map.at[idx, "Process_ID"] = f"'{process_id}"
                canon_name = canon_input
            else:
                canon_name = canon_map[canon_lower2id[ci_l]]

        if alias_raw_l in alias_lower_map or alias_raw_l in canon_lower2id:
            df_map.at[idx, "Std_Result"] = "Exists"
            continue
            
        try:
            with engine.begin() as conn:
                conn.execute(text(
                    "INSERT IGNORE INTO company_alias(alias, canonical_id, process_id) "
                    "VALUES (:a, :cid, :pid)"
                ), {"a": alias_raw, "cid": canon_lower2id[canon_name.lower()], "pid": process_id})
            alias_lower_map[alias_raw_l] = canon_name
            df_map.at[idx, "Std_Result"]   = "Added"
            df_map.at[idx, "Process_ID"] = f"'{process_id}"
        except Exception as e:
            print(f"⚠️ Alias insert error: {e}")

    df_map.to_csv(todo_f, index=False, encoding="utf-8-sig")

    with engine.begin() as conn2:
        ban_set2    = {r[0] for r in conn2.execute(text("SELECT alias FROM ban_list"))}
        rows2       = conn2.execute(text(
            "SELECT a.alias, c.canonical_name FROM company_alias a "
            "JOIN company_canonical c ON a.canonical_id=c.id"
        ))
        alias_map2  = {a: c for a, c in rows2}
        canon_set2  = {r[0] for r in conn2.execute(text("SELECT canonical_name FROM company_canonical"))}

    ban_lower2        = {b.lower() for b in ban_set2}
    alias_lower_map2  = {a.lower(): c for a, c in alias_map2.items()}
    canon_lower2orig2 = {c.lower(): c for c in canon_set2}

    comp_cols = [c for c in df_res.columns if c.startswith("company_")]

    def _norm_key(s: str) -> str:
        return re.sub(r"[^A-Za-z0-9]", "", str(s)).lower()

    changed_cells = 0
    for ridx in df_res.index:
        orig = df_res.loc[ridx, comp_cols].astype(str).tolist()
        vals_in = [v.strip() for v in orig if v.strip()]
        vals_out = []
        for nm in vals_in:
            key = nm.lower()
            if key in ban_lower2:
                continue
            if key in alias_lower_map2:
                nm = alias_lower_map2[key]
                changed_cells += 1
                key = nm.lower()
            elif key in canon_lower2orig2:
                corrected = canon_lower2orig2[key]
                if corrected != nm:
                    changed_cells += 1
                nm = corrected
            vals_out.append(nm)
        cleaned, seen = [], set()
        for nm in sorted(vals_out, key=len, reverse=True):
            k = _norm_key(nm)
            if any(k in kk or kk in k for kk in seen):
                continue
            cleaned.append(nm)
            seen.add(k)
        for i, col in enumerate(comp_cols):
            new_val = cleaned[i] if i < len(cleaned) else ""
            if str(df_res.at[ridx, col]) != new_val:
                changed_cells += 1
            df_res.at[ridx, col] = new_val

    df_res = dedup_company_cols(df_res)

    cute_box(
        f"已将最新映射应用到 result.csv（变更单元格约 {changed_cells} 个）",
        f"最新のマッピングを result.csv に適用しました（変更セル数 約 {changed_cells}）",
        "🛠️"
    )

    df_res.to_csv(res_f, index=False, encoding="utf-8-sig")

    cute_box(
        f"Step-3 完成，处理 {len(df_map)} 条映射，result.csv 已更新",
        f"Step-3 完了：{len(df_map)}件 処理済み，result.csv 更新完了",
        "🚀"
    )
    cute_box(
        f"本批次 Process ID：{process_id}",
        f"今回の Process ID：{process_id}",
        "📌"
    )