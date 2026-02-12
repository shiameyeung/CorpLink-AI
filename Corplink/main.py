# coding: utf-8
from .env_bootstrap import ensure_env

# 先确保环境
ensure_env()

from sqlalchemy import create_engine
from .env_bootstrap import cute_box
from .config import ask_mysql_url, configure_keywords, choose
from .step_extract import step1
from .step_company import step2
from .step_ai_autofill import step_ai_autofill
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
        
    mode = configure_keywords()
    
    if mode == "AUTO_START":
        print("\n" + "="*60)
        print("🚀 启动全自动模式 (Full Auto Mode)...")
        print("="*60)
        
        step1()
        step2(mysql_url)
        print("\n🤖 [Auto] 正在调用 AI 进行清洗 (Step 2.5)...")
        step_ai_autofill()
        print("\n💾 [Auto] 正在入库与标准化 (Step 3)...")
        step3(mysql_url)
        print("\n📊 [Auto] 正在生成分析报表 (Step 4)...")
        step4()
        
        print("\n🎉🎉🎉 全流程执行完毕！(Full Pipeline Complete)")
        return
    
    while True:
        choice = choose()

        if choice == "1":
            step1()
            step2(mysql_url)
            
            ai_cleaned_done = False

            while True:
                print("\n" + "="*60)
                
                if not ai_cleaned_done:
                    print("🎉 [Step 1-2] 完成 / 完了")
                    print("   文件已生成: result_mapping_todo.csv")
                    print("   ファイル生成完了: result_mapping_todo.csv")
                    print("-" * 60)
                    print("👉 接下来建议做什么？/ 次のステップ：")
                    print("   [a] 🤖 运行 AI 自动名寄せ (强烈推荐) / AI自動名寄せを実行 [推奨]")
                    print("   [b] ⚠️ 跳过清洗，直接入库・分析・結果出力 / そのままDB登録へ進む・分析・結果出力")
                else:
                    print("✨ [Step 2.5] AI名寄せ已完成 / AI名寄せ完了")
                    print("   请打开 result_mapping_todo.csv 简单检查一下，确认无误后继续。")
                    print("   名寄せ完了のresult_mapping_todo.csvを確認し、問題なければ次へ進んでください。")
                    print("-" * 60)
                    print("👉 下一步 / Next Step：")
                    print("   [b] 🚀 确认无误，执行入库・分析・結果出力 / 確認OK、DB登録・分析・結果出力")
                    print("   [a] 🔄 不满意，重跑 AI 清洗 / もう一度AIを実行")

                print("   [e] 👋 退出程序 / 一旦終了")
                print("="*60)
                
                sub_c = input("Input [a/b/e]: ").strip().lower()
                
                if sub_c == "a":
                    step_ai_autofill()
                    ai_cleaned_done = True
                    
                elif sub_c == "b":
                    step3(mysql_url)
                    step4()
                    print("🎉 完成！ result_adjacency_list.csvやpivot_table.csvを確認してください〜")
                    return
                    
                elif sub_c == "e":
                    print("👋 Bye!")
                    return

        elif choice == "2":
            step_ai_autofill()
            print("\n✅ 完成。您可以选择 [3] 进行入库，或输入 [e] 退出。\n✅ 完成。 [3] でDB登録・分析・結果出力、もしくは [e] で終了。")

        elif choice == "3":
            step3(mysql_url)
            step4()
            print("🎉 所有任务已完成 / 全てのタスクが完了しました")
            return

if __name__ == "__main__":
    main()