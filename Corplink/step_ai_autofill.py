# coding: utf-8
import json
from typing import List, Dict

import pandas as pd
from tqdm import tqdm
from openai import OpenAI

from .constants import BASE_DIR
from .env_bootstrap import cute_box

def ask_gpt_batch(batch_data: List[Dict], api_key: str) -> Dict:
    client = OpenAI(api_key=api_key)
    prompt = f"""
    You are a data cleaning expert for business strategy research. 
    Analyze the list of "alias" strings.

    Task: Determine the [Organizational Entity] behind the alias.
    
    [Allowed Categories] -> Set "is_company": true
    1. Commercial Companies (e.g., Toyota, Google, OpenAI)
    2. Educational Institutions (e.g., Harvard University, Tokyo High School)
    3. Government Bodies & Municipalities (e.g., Osaka Prefecture, Ministry of Economy)
    4. NGOs, NPOs, Associations (e.g., Red Cross, IEEE)
    
    [Special Mapping Rules for Products & IPs] -> Set "is_company": true
    If the 'alias' is a Product, Service, or Fictional Character/IP, DO NOT reject it. instead, map it to its OWNER Company.
    Examples:
    - "iPhone" -> is_company: true, clean_name: "Apple"
    - "ChatGPT" -> is_company: true, clean_name: "OpenAI"
    - "Mickey Mouse" -> is_company: true, clean_name: "Disney"
    - "Mario" -> is_company: true, clean_name: "Nintendo"
    - "Barbie" -> is_company: true, clean_name: "Mattel"

    [Forbidden Categories] -> Set "is_company": false
    1. General Nouns / Not Proper Nouns (e.g., "external researchers", "local governments", "our partners", "the committee", "anime", "video games")
    2. Job Titles / Departments (e.g., "CEO", "Sales Department")
    3. Individuals (unless the name refers to a sole proprietorship/studio)

    Rules for "clean_name":
    - Remove legal suffixes (Inc., Ltd., Corp., K.K., etc.).
    - If it is a Product/IP, use the OWNER Company Name.
    - Keep the full proper name (e.g., "University of Tokyo" -> "University of Tokyo").
    
    Input: {json.dumps(batch_data, ensure_ascii=False)}
    
    Output JSON format:
    {{
        "alias_original_text": {{ 
            "is_company": bool, 
            "clean_name": str, 
            "matches_advice": bool
        }}
    }}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0
        )
        return json.loads(response.choices[0].message.content)
    except:
        return {}

def step_ai_autofill():
    csv_path = BASE_DIR / "result_mapping_todo.csv"
    if not csv_path.exists():
        cute_box("找不到 result_mapping_todo.csv！", "ファイルが見つかりません", "❌")
        return

    key_file = BASE_DIR / ".openai_key"
    api_key = ""
    
    if key_file.exists():
        api_key = key_file.read_text().strip()
        print(f"🔑 已自动加载保存的 API Key: {api_key[:8]}...")
    
    if not api_key:
        api_key = input("请输入 OpenAI API Key (sk-...) / APIキーを输入: ").strip()
        if api_key:
            key_file.write_text(api_key)
            print("💾 API Key 已保存，下次无需输入。")

    if not api_key:
        print("❌ 未输入 Key，操作取消。")
        return

    print("⏳ 正在读取 CSV...")
    df = pd.read_csv(csv_path, dtype=str).fillna("")
    
    mask = df["Canonical_Name"] == ""
    rows_to_process = df[mask]
    
    if rows_to_process.empty:
        print("✨ 所有行的 Canonical_Name 都已填好，无需处理！")
        return

    print(f"🤖 准备处理 {len(rows_to_process)} 条数据...")
    
    batch_size = 30
    updates = {}
    
    data_list = []
    for idx, row in rows_to_process.iterrows():
        data_list.append({
            "index": idx,
            "alias": row["Alias"],
            "advice": row["Advice"]
        })

    for i in tqdm(range(0, len(data_list), batch_size), desc="GPT Cleaning"):
        batch = data_list[i : i + batch_size]
        gpt_input = [{"alias": item["alias"], "advice": item["advice"]} for item in batch]
        gpt_res = ask_gpt_batch(gpt_input, api_key)
        
        for item in batch:
            alias = item["alias"]
            idx = item["index"]
            
            adv_id = df.at[idx, "Adviced_ID"]
            
            if alias in gpt_res:
                res = gpt_res[alias]
                
                if not res.get("is_company", False):
                    updates[idx] = "0"
                else:
                    if df.at[idx, "Advice"] and df.at[idx, "Adviced_ID"] and res.get("matches_advice", False):
                        updates[idx] = df.at[idx, "Adviced_ID"]
                    else:
                        updates[idx] = res.get("clean_name", alias)

    print("💾 正在保存结果...")
    for idx, val in updates.items():
        df.at[idx, "Canonical_Name"] = val
        
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    cute_box(
        f"✅ 自动填写完成！已更新 {len(updates)} 行", 
        f"自動入力完了！{len(updates)} 行を更新しました", 
        "🎉"
    )