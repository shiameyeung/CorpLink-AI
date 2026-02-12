# coding: utf-8
import itertools
import pandas as pd
from tqdm import tqdm

from .constants import BASE_DIR, MAX_COMP_COLS
from .env_bootstrap import cute_box

def step4():
    df = pd.read_csv(BASE_DIR / "result.csv", dtype=str).fillna("")
    rows = []
    
    meta_cols = ["Tier_1", "Tier_2", "Filename", "Date", 
                 "Title", "Publisher", "Sentence", 
                 "Hit_Count", "Matched_Keywords"]

    for _, r in tqdm(df.iterrows(), desc="生成邻接表", total=len(df)):
        comps = [r[f"company_{i}"] 
                 for i in range(1, MAX_COMP_COLS+1) 
                 if r[f"company_{i}"].strip()]
        
        current_meta = {col: r.get(col, "") for col in meta_cols}

        for a, b in itertools.permutations(comps, 2):
            row_data = {
                "company_a": a,
                "company_b": b,
                "value": 1,
            }
            row_data.update(current_meta)
            rows.append(row_data)

    out = pd.DataFrame(rows)

    if not out.empty:
        output_cols = [c for c in meta_cols if c in out.columns] + ["company_a", "company_b"]
        out[output_cols].to_csv(
            BASE_DIR / "result_adjacency_list.csv",
            index=False, encoding="utf-8-sig"
        )
    else:
        output_cols = meta_cols + ["company_a", "company_b"]
        pd.DataFrame(columns=output_cols).to_csv(
            BASE_DIR / "result_adjacency_list.csv",
            index=False, encoding="utf-8-sig"
        )

    cute_box(
        "Step4 已生成邻接表(含元数据)：result_adjacency_list.csv",
        "Step4 隣接リスト(メタデータ付)を生成しました：result_adjacency_list.csv",
        "📋"
    )

    if not out.empty:
        pivot = out.pivot_table(
            index="company_a",
            columns="company_b",
            values="value",
            aggfunc="sum",
            fill_value=""
        )
    else:
        pivot = pd.DataFrame()

    pivot.to_csv(
        BASE_DIR / "pivot_table.csv",
        encoding="utf-8-sig"
    )
    cute_box(
        "Step4 已生成透视表：pivot_table.csv",
        "Step4 ピボットテーブルを生成しました：pivot_table.csv",
        "📊"
    )