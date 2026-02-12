CorpLink-AI: 非構造化テキストからの企業間ネットワーク自動抽出・分析システム

CorpLink-AIは、国際経営戦略論の研究において、数千～数万件規模のニュースリリースやレポート（非構造化テキスト）から、企業間の提携・協力関係を効率的かつ高精度に抽出し、構造化データベースを構築するために開発された自動データ処理パイプライン（ETL Pipeline）です。

従来の「キーワード検索」や「手作業による名寄せ」の限界を突破するため、最新の小規模言語モデル（SLM）と大規模言語モデル（LLM）を組み合わせたハイブリッドアーキテクチャを採用しています。

堅牢なデータ処理ロジック (Robust Engineering)

実データに含まれる「汚れ」や「ノイズ」に対応するための工夫を随所に実装しています。

アンカー検証機能: ニュース本文中の小見出しを「発行元（Publisher）」と誤認しないよう、日付フォーマットをアンカー（目印）として記事の開始位置を特定する検証ロジックを搭載。

IP/製品名の帰属解決: 「iPhone」「ミッキーマウス」などの製品・IP名が抽出された場合、単に除外するのではなく、その権利元企業（Apple、Disneyなど）へ自動マッピングするロジックをプロンプトに組み込みました。

🛠️ 主な機能 (Features)
✅ Step 1: 高度なテキスト抽出 & フィルタリング

マルチモード対応: 従来の「キーワードマッチング」に加え、「AI意味論的フィルタリング」モードを搭載。SBERTを用いて「戦略的提携」に関連する文脈のみを高精度に抽出します。

日付・発行元の自動特定: 複雑なフォーマットのWord/PDF文書から、記事ごとのメタデータ（日付、発行元）を正確にパースします。

✅ Step 2: インテリジェントなデータ洗浄 (Smart Cleaning)

Fuzzy + AI ハイブリッド照合:

まず RapidFuzz を用いて、既存データベース内の企業名と字面が似ているもの（表記ゆれ）を高速マッチング。

マッチしない場合、SentenceTransformer で意味的な類似性を計算し、「Google」と「Alphabet」のような関連性を検出。

GPT Auto-fill (自動名寄せ):

未知の企業名に対しては、OpenAI API (GPT-4o-mini) を呼び出し、「企業か否かの判定」「正式名称への正規化」「IPの親会社特定」を全自動で行います。

✅ Step 3 & 4: データベース構築とネットワーク分析

MySQLへの構造化保存: 抽出・正規化されたデータを、canonical_name（正規名）とalias（別名）のリレーショナル構造で保存。

ネットワークグラフ生成: 企業間の共起関係に基づき、隣接リスト（Adjacency List）とピボットテーブルを自動生成し、社会ネットワーク分析（SNA）ツールへ即座にインポート可能な形式で出力します。

💻 技術スタック (Tech Stack)

Language: Python 3.11+

NLP Models: spaCy, SentenceTransformers (all-MiniLM-L6-v2), GPT-4o-mini

Libraries: PyTorch, Pandas, SQLAlchemy, python-docx, RapidFuzz, OpenAI

Database: MySQL (MariaDB)

# ガイド

# 初回
## NA_launcher.pyをダウンロードする。
https://github.com/shiameyeung/NA/blob/main/launcher.py

## （Windowsのみ、macOSは不要）以下リンクからダウンロード・インストール  
https://aka.ms/vs/17/release/vc_redist.x64.exe

## Pythonを用意  
Python 3.11.9  
**Windows：**  
https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe  
**macOS：**  
https://www.python.org/ftp/python/3.11.9/python-3.11.9-macos11.pkg

> インストール時は「Add to PATH」に必ずチェックを入れてください

## 環境設定１：プロジェクトフォルダ作成

**macOS（ターミナル）**  
```bash
mkdir -p ~/NA_project && cd ~/NA_project
```
**Windows（PowerShell）**  
```powershell
mkdir %USERPROFILE%\NA_project
cd %USERPROFILE%\NA_project
```

## 環境設定２：仮想環境の作成
```bash
python -m venv NA_env
```

## 環境設定３：仮想環境を有効化

- **macOS：**
  ```bash
  source NA_env/bin/activate
  ```
- **Windows：**
  ```powershell
  %USERPROFILE%\NA_project> NA_env\Scripts\activate
  ```

## 環境設定４：必要パッケージのインストール
```bash
pip install -U pip setuptools wheel
```

## ランチャー起動手順
1. ターミナル（またはPowerShell）で `python `（後ろにスペース）と入力  
2. `NA_launcher.py` をドラッグ＆ドロップし、Enterキーを押す  
3. 完了するまで待ちます

---

# 毎回の実行手順

1. `NA_launcher.py` と対象の `.DOCX` ファイルを同じフォルダに置く  
2. 仮想環境を有効化  
   - macOS: `source NA_env/bin/activate`  
   - Windows: `.\NA_env\Scripts\Activate.ps1`  
3. ターミナルで `python `（後ろにスペース）と入力  
4. `NA_launcher.py` をドラッグ＆ドロップしてEnter  
5. **初回のみ**：キーコードを貼り付けてEnter  
6. 「1」と入力してEnter  
7. 完了後、`NA_mapping_todo.csv` を開き、F列（canonical_name）を記入  
   - **参考**  
     - Bad_rate：値が高いほど、偽企業名の可能性高い  
     - Advice：既存の正規企業名とマッチした候補  
     - Advice ID：正規企業名のID
     - canonical_name表で現存の正規企業名一覧を参考
   - **入力ルール**  
     - 偽企業名 → `0`  
     - 既存の正規企業名 → ID（canonical_name表またはAdvice ID）  
     - 新規の正規企業名 → 英数字  
   - **数分ごとに必ず保存！**

8. 保存してCSVを閉じる  
9. ターミナルに戻り  
   - プログラムがまだ動いていれば「2」と入力→Enter  
   - すでに終了していれば、再度 `python ` → ドラッグ＆ドロップ → 「2」と入力→Enter

---

# 大完成！結果を見ましょう 🎉

---

## 📧 サポート

ご不明点やご意見は以下までお問い合わせください：  
作者：楊 天楽 (Shiame Yeung)  
1@yotenra.com


協力：李 宗昊、李 佳璇
