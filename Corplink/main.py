# coding: utf-8
from .env_bootstrap import ensure_env
ensure_env()

from sqlalchemy import create_engine
from .env_bootstrap import cute_box
from .config import ask_mysql_url, wizard, apply_options_to_state
from .options import AILevel
from .step_extract import step1
from .step_company import step2
from .step_ai_autofill import step_ai_autofill, step_ai_suggest  # 后面会新增 step_ai_suggest
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

    # 先跑 Step1-2（Lexis）
    step1()
    step2(mysql_url)

    if opts.ai_level == AILevel.MANUAL:
        print("✅ 已完成 Step1-2。请手动编辑 result_mapping_todo.csv 的 Canonical_Name 后再继续执行 Step3-4。")
        return

    if opts.ai_level == AILevel.ASSIST:
        print("🤖 正在生成 AI 建议列（不覆盖 Canonical_Name）...")
        step_ai_suggest()   # 新函数：写新列
        print("✅ 已生成建议列。请检查 result_mapping_todo.csv，然后再执行 Step3-4。")
        return

    # AUTO
    print("\n🤖 [Auto] 正在调用 AI 进行清洗 (Step 2.5)...")
    step_ai_autofill()
    print("\n💾 [Auto] 正在入库与标准化 (Step 3)...")
    step3(mysql_url)
    print("\n📊 [Auto] 正在生成分析报表 (Step 4)...")
    step4()
    print("\n🎉🎉🎉 全流程执行完毕！(Full Pipeline Complete)")

if __name__ == "__main__":
    main()
