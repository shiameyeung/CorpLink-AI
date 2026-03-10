# CorpLink-AI

# 以下は英語、日本語は後です。

# Corp-link AI Overview

## About the Core Code

Inter-organizational relationships, such as those between enterprises, are very important in business decision-making

There is a need to research and analyze the characteristics of inter-enterprise relationships, find commonalities, write papers, and provide methodologies

The analysis requires a large amount of paired relationship data

English articles in commercial news databases implicitly contain a large amount of relationship information

Direct full-text analysis: USD 25 / 1,000,000 English words of news data

It is too expensive, a cheaper solution is needed

Import docx or rtf files

Local full-text search to pinpoint sentences containing keywords indicating relationships, such as cooperat and bind

Use spaCy and the en_core_web_sm plugin on sentences to extract preliminary suspected organization names

Process preliminary suspected organization names using Sentence-Transformers and RapidFuzz for filtering and fuzzy matching

Further compare and match with existing ban data tables and suspected organization name-regular organization name data tables in the MySQL database
* ban data table: Used to filter out suspected organization names that have been marked as non-organization names
* Suspected organization name-regular organization name data table: For existing suspected organization names, replace them directly with regular organization names

For suspected organization names that do not appear in the ban data table or the suspected organization name-regular organization name data table:
* Call the 4o-mini model of the OpenAI API to obtain regular organization names. Regarding costs:
    * No historical data of similar industries or scenarios exists in the database: USD 0.006 / 1,000,000 English words of news data
        * The cost is 1/4,000th of full-text recognition
    * Historical data of similar industries or scenarios exists in the database: USD 0.0015 / 1,000,000 English words of news data
        * The cost is 1/17,000th of full-text recognition
    * Exactly matching historical data exists in the database: 0 cost

Save the current processing results to the MySQL database for priority use of existing data in subsequent processing

Further reduce the number of tokens for subsequent OpenAI API calls, thereby further lowering costs

Summary: Build a localized automated processing tool for "news data → organizational relationships" that becomes smarter and cheaper the more it is used


## About the Accompanying Web APP

Running python files locally requires a certain operational threshold (configuring the environment, code files, etc.)

Provide a one-stop, one-click APP to simplify use and lower the threshold

Users only need to upload the news data file packaged as a .zip, select processing parameters, and input the API key

Click to start processing, wait a few minutes to hours, and then download the results


# Corp-link AI 概要

## コアコードについて

企業等の組織間関係は経営意思決定において非常に重要である

企業間関係の特徴を研究・分析し、共通点を探り、論文を執筆し、方法論を提供する必要がある

その分析には大量のペア関係データが必要である

商用ニュースデータベース内の英語記事には大量の関係情報が暗黙的に含まれている

直接の全文分析：USD 25 / 1,000,000 英語文字ニュースデータ

コストが高すぎるため、安価なソリューションが必要である

docxまたはrtfファイルをインポートする

ローカルで全文検索を行い、cooperatやbindなど関係を示すキーワードを含む文を特定する

文に対してspaCy、en_core_web_smプラグインを使用し、初期の疑似組織名を抽出する

初期の疑似組織名に対し、Sentence-TransformersやRapidFuzzを使用してフィルタリングとあいまいマッチングを行う

さらに、MySQLデータベースの既存のbanデータテーブル、疑似組織名-正規組織名データテーブルと比較・マッチングを行う
* banデータテーブル：すでに非組織名としてマークされている疑似組織名を除外するために使用する
* 疑似組織名-正規組織名データテーブル：既存の疑似組織名について、直接正規組織名に置換する

banデータテーブル、疑似組織名-正規組織名データテーブルに存在しない疑似組織名について：
* OpenAI APIの 4o-mini モデルを呼び出し、正規組織名を取得する。費用について：
    * データベースに類似の業界・シナリオの履歴データが存在しない場合：USD 0.006 / 1,000,000 英語文字ニュースデータ
        * かかる費用は全文認識の4,000分の1
    * データベースに類似の業界・シナリオの履歴データが存在する場合：USD 0.0015 / 1,000,000 英語文字ニュースデータ
        * かかる費用は全文認識の17,000分の1
    * データベースに完全一致する履歴データが存在する場合：費用 0

今回の処理結果をMySQLデータベースに保存し、以後の処理で既存データを優先的に使用できるようにする

以降のOpenAI API呼び出し時のトークン数をさらに削減し、それによりさらなるコスト削減を図る

まとめ：使えば使うほどスマートになり、低コストになるローカライズされた「ニュースデータ→組織関係」の自動処理ツールを構築する


## 付属の Web APP について

ローカルで python ファイルを実行するには、一定の操作ハードルがある（環境構築、コードファイルなど）

ワンストップ、ワンクリックの APP を提供し、使用を簡素化してハードルを下げる

ユーザーは .zip に圧縮されたニュースデータファイルをアップロードし、処理パラメータを選択し、API key を入力するだけでよい

「処理開始」をクリックし、数分から数時間待って、結果をダウンロードするだけで完了する
