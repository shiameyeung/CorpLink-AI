# CorpLink-AI

# 以下は英語、日本語は後です。

# Corp-link AI Overview

## About the Core Code

### Purpose

A research prototype that converts news articles into pairs of company names and adjacency matrices for network analysis. It organizes information from news articles into data for studying patterns in intercompany relationships.

### Processing workflow

1. Read news articles from DOCX or RTF files.
2. Select sentences containing keywords that indicate relationships, such as `cooperat` and `bind`, and use spaCy’s `en_core_web_sm` to extract candidate organization names.
3. Use Sentence-Transformers and RapidFuzz to filter candidates and match similar names.
4. Reuse saved decisions by consulting the exclusion results and name mappings stored in MySQL. The exclusion table stores decisions about candidates that should not be treated as organization names; the name-mapping table links candidate names to normalized names.
5. Use `gpt-4o-mini` to assess candidates that remain unresolved after matching, then save the name mappings and exclusion decisions.
6. Export company-name pairs and adjacency matrices as CSV files for subsequent network analysis.

### Model calls and result reuse

The pipeline prioritizes local matching and saved results, calling the model only for candidates that need further judgment. It reuses these results in subsequent processing to reduce the need to assess the same names repeatedly.

API usage varies with the input data, repeated names, and matches with previously saved data.


## About the Accompanying Web APP

The web interface brings together file input, parameter settings, and result downloads in a browser. Upload a ZIP file containing the news articles, enter the processing parameters and API key, and download the results when processing is complete.

This repository contains the code for a research prototype. Set up the runtime environment and connection settings, then verify that it works in your environment before use.

## Development approach

I developed this prototype to support news analysis in my research lab. I integrated code suggestions from Gemini and ChatGPT and deployed it using Git.


# Corp-link AI 概要

## コアコードについて

### 用途

ニュース記事から企業名のペアと隣接行列を作成する、ネットワーク分析向けの研究用プロトタイプ。企業間関係の特徴を調べるため、ニュース記事に含まれる情報を分析用データに整理する。

### 処理の流れ

1. DOCXまたはRTFのニュース記事を読み込む。
2. `cooperat`や`bind`など、関係を示すキーワードを含む文を選び、spaCyの`en_core_web_sm`で組織名の候補を抽出する。
3. Sentence-TransformersとRapidFuzzを使い、候補を絞り込み、表記の近い名称を照合する。
4. MySQLに保存した除外判定の結果と名称の対応表を参照し、保存済みの判定結果を再利用する。除外表には組織名として扱わない候補の判定結果を、対応表には名称候補と正規化した名称の対応関係を保存する。
5. 照合で対応が確定しなかった名称候補を`gpt-4o-mini`で判定し、名称の対応関係と除外判定の結果を保存する。
6. 企業名のペアと隣接行列をCSVとして出力し、後続のネットワーク分析に利用する。

### モデルの呼び出しと結果の再利用

ローカルの照合と保存済みの結果を優先し、追加の判断が必要な候補に絞ってモデルを呼び出す。得られた結果を以後の処理で再利用し、同じ名称についての判定を繰り返す手間を減らす。

APIの利用量は、入力データ、名称の重複、保存済みデータとの一致状況によって変わる。

## 付属の Web APP について

ファイルの入力、パラメーターの設定、結果のダウンロードをブラウザーで行える形にまとめた。ニュース記事をまとめたZIPファイルをアップロードし、処理パラメーターとAPIキーを入力する。処理完了後に結果をダウンロードする。

このリポジトリでは研究用プロトタイプのコードを公開している。実行環境の準備と接続設定を行い、動作を確認して利用する。

## 開発の進め方

研究室でのニュース分析を支えるために開発した。GeminiとChatGPTから得たコード案を統合し、Gitを使ってデプロイした。
