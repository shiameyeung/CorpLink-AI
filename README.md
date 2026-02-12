# CorpLink-AI
**非構造化テキストから企業間ネットワークを自動抽出・分析するAIパイプライン**

CorpLink-AI は、ニュースリリース・レポート等の非構造化テキストから、企業間の提携・協力・投資・M&A 関係を抽出し、データベースに標準化したうえでネットワーク分析用の出力（隣接リスト・ピボット）を生成する研究用ツールです。

---

## ✨ 特徴

- **キーワード抽出 / 意味論フィルタ**に対応（SBERT）
- **Word (.docx)** と **Factiva (.rtf)** の両モード対応
- **企業名の自動正規化**（RapidFuzz + SentenceTransformer + GPT）
- **MySQL に名寄せデータを保存**
- **ネットワーク分析用CSVを自動生成**

---

## 📦 主な機能（Step構成）

### Step 1：文抽出
- `.docx` または `.rtf` から文を抽出
- キーワード or セマンティックフィルタでヒット文を抽出

### Step 2：企業抽出と候補生成
- spaCy NER + 既存DB + フィルタリング
- `result.csv` / `result_mapping_todo.csv` を生成

### Step 2.5（オプション）：AI補完
- GPT による **企業判定・正規名推定・IP/製品の親企業推定**
- `ASSIST` モード：新列に提案だけを書き込み
- `AUTO` モード：自動で Canonical_Name を埋める

### Step 3：標準化（DB反映）
- `result_mapping_todo.csv` を参照して DB を更新
- `result.csv` を最新の正規名で再生成

### Step 4��ネットワーク生成
- 隣接リスト `result_adjacency_list.csv`
- ピボットテーブル `pivot_table.csv`

---

## 🧠 実行モード

起動時に以下を選択します：

1. **MANUAL**：AIを使わず Step1→2 まで
2. **ASSIST**：AI提案列だけ生成（上書きしない）
3. **AUTO**：AIで補完 → DB反映 → ネットワーク生成まで全自動

---

## 🔧 必要環境

- Python **3.11+**
- MySQL（MariaDB）
- 主要ライブラリ：
  - pandas / sqlalchemy / pymysql
  - spacy / sentence-transformers / torch
  - openai / rapidfuzz / python-docx / striprtf

---

## 🚀 実行方法

### 1. ランチャー実行
```
python launcher.py
```

### 2. MySQL 接続
```
user:pass@host
```

### 3. モード選択
- キーワードモード
- AIレベル
- 抽出モード（Lexis / Factiva）

---

## 📂 出力ファイル

| ファイル | 内容 |
|---------|------|
| result.csv | 企業抽出結果 |
| result_mapping_todo.csv | 名寄せ入力用 |
| result_adjacency_list.csv | 隣接リスト |
| pivot_table.csv | ピボット表 |

---

## ⚠️ メモ

- `result_mapping_todo.csv` の入力ルール：
  - `0` → BAN
  - 数字 → canonical_id として処理
  - 文字列 → 新規 canonical_name として登録

---

## ✉️ サポート

作者: Shiame Yeung  
お問い合わせ: 1@yotenra.com
