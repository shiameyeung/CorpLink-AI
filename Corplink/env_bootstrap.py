# 原作者：杨天乐@关西大学 / Author: Shiame Yeung@Kansai University / 作成者：楊　天楽@関西大学
#!/usr/bin/env python3
# coding: utf-8

import sys
import subprocess
import os

def cute_box(cn: str, jp: str, icon: str = "🌸") -> None:
    """
    多行也能对齐的可爱中/日双语框
    cn: 中文提示（可以多行，用 '\\n' 分隔）
    jp: 日文提示（可以多行）
    icon: 每行开头和结尾的小表情
    """
    lines = []
    for segment in (cn, jp):
        for ln in segment.split("\n"):
            ln = ln.strip()
            lines.append(f"{icon} {ln} {icon}")

    width = max(len(ln) for ln in lines)
    border = "─" * width

    print(f"╭{border}╮")
    for ln in lines:
        print("│" + ln.ljust(width) + "│")
    print(f"╰{border}╯")

def ensure_env() -> None:
    """
    环境自检与自动修复程序
    1. 检查所有必要的库 (包括 OpenAI, GLiNER, RapidFuzz 等)
    2. 缺失则自动调用 pip 安装
    3. 安装完成后自动重启脚本，实现无缝体验
    """
    import pkg_resources
    from pkg_resources import DistributionNotFound, VersionConflict

    REQUIRED_PACKAGES = [
        "pandas", 
        "tqdm", 
        "requests",
        "packaging",
        "sqlalchemy", 
        "pymysql",
        "python-docx", 
        "rapidfuzz",
        "openai>=1.0.0",
        "gliner",
        "sentence-transformers",
        "torch",
        "transformers",
        "spacy",
    ]

    py_major, py_minor = sys.version_info[:2]
    if (py_major, py_minor) >= (3, 13):
        pass

    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            pkg_resources.require(pkg)
        except (DistributionNotFound, VersionConflict):
            missing.append(pkg)

    try:
        import spacy
        if not spacy.util.is_package("en_core_web_sm"):
            missing.append("spacy_model:en_core_web_sm")
    except ImportError:
        pass

    if missing:
        cute_box(
            f"检测到缺失依赖，正在自动安装...\n缺失项: {', '.join(missing)}",
            f"不足している依存関係を検出しました。自動インストール中...\n対象: {', '.join(missing)}",
            "📦"
        )
        
        pip_pkgs = [p for p in missing if not p.startswith("spacy_model:")]
        spacy_models = [p for p in missing if p.startswith("spacy_model:")]

        if pip_pkgs:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install"] + pip_pkgs)
            except subprocess.CalledProcessError as e:
                cute_box(f"安装失败: {e}\n请尝试手动运行: pip install {' '.join(pip_pkgs)}", 
                         "インストールに失敗しました。手動で実行してください。", "❌")
                sys.exit(1)

        for model in spacy_models:
            model_name = model.split(":")[1]
            print(f"⬇️ Downloading spaCy model: {model_name}...")
            subprocess.check_call([sys.executable, "-m", "spacy", "download", model_name])

        cute_box(
            "依赖安装完成！正在自动重启程序...",
            "インストール完了！プログラムを自動再起動します...",
            "🔄"
        )
        os.execv(sys.executable, [sys.executable] + sys.argv)