# 原作者：杨天乐@关西大学 / Author: Shiame Yeung@Kansai University / 作成者：楊　天楽@関西大学
#!/usr/bin/env python3
# coding: utf-8

import requests
import sys

URL = "https://raw.githubusercontent.com/shiameyeung/NA/main/NA_main.py"

def main():
    print("🔄 正在从GitHub获取最新版脚本...")
    try:
        resp = requests.get(URL)
        resp.raise_for_status()
        code = resp.text
    except Exception as e:
        print("❌ 下载失败:", e)
        sys.exit(1)

    print("✅ 下载完成，正在执行...\n")

    # 直接在当前进程里执行脚本
    exec(code, globals())

if __name__ == "__main__":
    main()
