# 原作者：杨天乐@关西大学 / Author: Shiame Yeung@Kansai University / 作成者：楊　天楽@関西大学
#!/usr/bin/env python3
# coding: utf-8

import os
import sys
import requests
import runpy
from pathlib import Path

RAW_BASE = "https://raw.githubusercontent.com/shiameyeung/CorpLink-AI/main"

FILES = [
    "main.py",
    "Corplink/__init__.py",
    "Corplink/config.py",
    "Corplink/constants.py",
    "Corplink/env_bootstrap.py",
    "Corplink/main.py",
    "Corplink/model_utils.py",
    "Corplink/state.py",
    "Corplink/step_ai_autofill.py",
    "Corplink/step_company.py",
    "Corplink/step_extract.py",
    "Corplink/step_network.py",
    "Corplink/step_standardize.py",
    "Corplink/text_utils.py",
]

def download_file(rel_path: str):
    url = f"{RAW_BASE}/{rel_path}"
    dest = Path(rel_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    print(f"⬇️ Downloading {rel_path}...")
    r = requests.get(url)
    r.raise_for_status()
    dest.write_bytes(r.content)

def main():
    print("🔄 正在从GitHub获取最新版脚本与模块...")
    try:
        for f in FILES:
            download_file(f)
    except Exception as e:
        print("❌ 下载失败:", e)
        sys.exit(1)

    print("✅ 下载完成，正在执行...\n")
    runpy.run_path("main.py", run_name="__main__")

if __name__ == "__main__":
    main()
