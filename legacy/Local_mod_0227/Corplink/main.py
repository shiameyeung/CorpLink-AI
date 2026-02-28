# coding: utf-8
from .env_bootstrap import ensure_env
ensure_env()

from sqlalchemy import create_engine
from .env_bootstrap import cute_box
from .config import ask_mysql_url, wizard, apply_options_to_state
from .options import AILevel
from .constants import BASE_DIR

from .step_extract import step1
from .step_company import step2
from .step_ai_autofill import step_ai_autofill, step_ai_suggest
from .step_standardize import step3
from .step_network import step4

def main():
    mysql_url = ask_mysql_url()
    try:
        create_engine(mysql_url).connect().close()
        print("✅ 数据库连接成功 / データベース接続成功")
    except Exception as e:
        cute_box(f"数据库连接失败：{e}", f"データベース接続 失敗：{e}", "❌")
        return

    opts = wizard()
    apply_options_to_state(opts)

    todo_path = BASE_DIR / "result_mapping_todo.csv"

    # ====== 第二次运行：检测到 todo 已存在，允许直接从 Step3-4 继续 ======
    if todo_path.exists():
        ans = input("检测到 result_mapping_todo.csv 已存在。是否跳过 Step1-2，直接继续 Step3-4？(y/N): ").strip().lower()
        if ans == "y":
            step3(mysql_url)
            step4()
            print("🎉 Step3-4 已完成。")
            return

    # ====== 正常流程：先跑 Step1-2 ======
    step1()
    step2(mysql_url)

    # ====== MANUAL：一次运行内询问是否继续 ======
    if opts.ai_level == AILevel.MANUAL:
        print("✅ 已完成 Step1-2。请手动编辑 result_mapping_todo.csv 的 Canonical_Name。")
        ans = input("填完后是否继续执行 Step3-4？(y/N): ").strip().lower()
        if ans == "y":
            step3(mysql_url)
            step4()
            print("🎉 Step3-4 已完成。")
        else:
            print("👋 已退出。下次运行可选择直接继续 Step3-4。")
        return

    # ====== ASSIST：生成新列后退出（你也可以同样问 y 继续） ======
    if opts.ai_level == AILevel.ASSIST:
        print("🤖 正在生成 AI 建议列（不覆盖 Canonical_Name）...")
        step_ai_suggest()
        print("✅ 已生成建议列。请检查/必要时手动修改 Canonical_Name。")
        ans = input("是否继续执行 Step3-4？(y/N): ").strip().lower()
        if ans == "y":
            step3(mysql_url)
            step4()
            print("🎉 Step3-4 已完成。")
        return

    # ====== AUTO：全自动 ======
    print("\n🤖 [Auto] 正在调用 AI 进行清洗 (Step 2.5)...")
    step_ai_autofill()
    print("\n💾 [Auto] 正在入库与标准化 (Step 3)...")
    step3(mysql_url)
    print("\n📊 [Auto] 正在生成分析报表 (Step 4)...")
    step4()
    print("\n🎉🎉🎉 全流程执行完毕！(Full Pipeline Complete)")

if __name__ == "__main__":
    main()
