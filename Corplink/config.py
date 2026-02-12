# coding: utf-8
from pathlib import Path
from .env_bootstrap import cute_box
from .constants import PRESET_KEYWORDS_2025, ANCHOR_TEXT
from . import state

def ask_mysql_url() -> str:
    key_file = Path(__file__).with_name(".db_key")
    if key_file.exists():
        key = key_file.read_text().strip()
    else:
        key = input("请输入秘钥/キーを入力してください：user:pass@host\n>>>>>> ").strip()
        key_file.write_text(key)
    return f"mysql+pymysql://{key}:3306/na_data?charset=utf8mb4" 

def choose() -> str:
    cute_box(
        "CorpLink-AI 自动化处理系统\n"
        "------------------------------------------------\n"
        "① [开始] 提取数据 (Step 1-2)\n"
        "   - 从文档提取句子 -> 初步识别 -> 生成待清洗表\n\n"
        "② [清洗] AI 自动名寄せ (Step 2.5)\n"
        "   - 调用 GPT API 自动清洗/标准化 result_mapping_todo.csv\n\n"
        "③ [完成] 入库与分析 (Step 3-4)\n"
        "   - 读取清洗后的表 -> 存入数据库 -> 生成网络分析表\n"
        "------------------------------------------------\n"
        "作者：杨天乐 @ 关西大学 伊佐田研究室",
        
        "CorpLink-AI 自動化処理システム\n"
        "------------------------------------------------\n"
        "① [開始] データ抽出・一次処理 (Step 1-2)\n"
        "   - ドキュメント解析 -> 企業名抽出 -> 候補リスト生成\n\n"
        "② [浄化] AIによる自動名寄せ (Step 2.5)\n"
        "   - GPT APIを利用して、表記ゆれやノイズを自動修正\n\n"
        "③ [完了] DB登録・ネットワーク分析 (Step 3-4)\n"
        "   - クリーニング済みデータをDBへ登録 -> 分析用テーブル出力\n"
        "------------------------------------------------\n"
        "作成者：楊 天楽　協力：李 宗昊 李 佳璇 @関西大学",
        "🤖"
    )
    
    while True:
        c = input("👉 请输入功能序号 / 番号を入力してください (1/2/3): ").strip()
        if c in {"1", "2", "3"}:
            return c
        print("❌ 输入无效，请重新输入 / 無効な入力です")

def configure_keywords():
    global ANCHOR_TEXT
    cute_box(
        "【配置】请选择信息抽取的模式：\n"
        "0. [一键通] 默认关键词 + 全自动执行 (Step 1-4) 🚀\n"
        "1. 关键词模式: 2025 AI x Healthcare (默认)\n"
        "2. 关键词模式: 自定义输入\n"
        "3. AI语义模式: 语义向量匹配 (Beta)(sentence-transformers/all-MiniLM-L6-v2)",
        
        "【設定】情報抽出モードを選択してください：\n"
        "0. [ワンクリック] デフォルトキーワードモード: + 全自動実行 (Step 1-4) 🚀\n"
        "1. キーワードモード: 2025 AI x ヘルスケア (デフォルト)\n"
        "2. キーワードモード: カスタム入力 (その他)\n"
        "3. AIモード: ベクトル類似度マッチング (Beta)(sentence-transformers/all-MiniLM-L6-v2)",
        "⚙️"
    )
    
    choice = input("👉 请输入 / 番号を入力 (0/1/2/3) [Default: 1]: ").strip()
    
    if choice == "0":
        state.KEYWORD_ROOTS = PRESET_KEYWORDS_2025
        print("✅ [System] 已加载默认关键词集，准备启动全自动模式...")
        return "AUTO_START"
    elif choice == "3":
        state.USE_SEMANTIC_FILTER = True
        print("\n✅ [System] AI语义筛选已启用 (Model: sentence-transformers/all-MiniLM-L6-v2)")
        print("   [System] AIフィルタリングが有効になりました")
        return None
    elif choice == "2":
        print("\n👉 请输入自定义关键词 (逗号分隔) / カスタムキーワードを输入 (カンマ区切り):")
        raw_input = input(">>>>>> ").strip()
        try:
            custom_keys = [k.strip().strip("'").strip('"') for k in raw_input.split(',') if k.strip()]
            if not custom_keys: 
                raise ValueError
            state.KEYWORD_ROOTS = custom_keys
            print(f"✅ [System] 已加载 {len(state.KEYWORD_ROOTS)} 个自定义关键词")
        except:
            print("❌ [Error] 格式错误，已回退到默认模式 / フォーマットエラー、デフォルトに戻ります")
            state.KEYWORD_ROOTS = PRESET_KEYWORDS_2025
        return None
    else:
        state.KEYWORD_ROOTS = PRESET_KEYWORDS_2025
        print("✅ [System] 已加载默认关键词集 / デフォルトキーワードをロードしました")
        return None