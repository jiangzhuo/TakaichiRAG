# 高市早苗 RAGシステム

[高市早苗議員の公式ウェブサイト](https://www.sanae.gr.jp/)から情報を収集し、RAG（Retrieval-Augmented Generation）システムを構築するプロジェクトです。

## 機能

- 🌐 **Webスクレイピング**: 高市早苗の公式サイトから自動的にコンテンツを収集
- 🔍 **日本語対応RAG**: OpenAIのAPIとRAGLiteを使用した高精度な質問応答システム
- 💾 **DuckDB統合**: 軽量で高速なローカルデータベース
- 🎌 **完全な日本語サポート**: 日本語に最適化されたembeddingとreranker

## 収集対象ページ

- 基本理念 (https://www.sanae.gr.jp/idea.html)
- 政治姿勢 (https://www.sanae.gr.jp/posture.html)
- 実績 (https://www.sanae.gr.jp/results.html)
- 記者会見 (https://www.sanae.gr.jp/kaiken.html)
- コラム (https://www.sanae.gr.jp/column.html)

## セットアップ

### 1. 必要条件

- Python 3.10以上
- OpenAI APIキー

### 2. インストール

```bash
# リポジトリをクローン
cd TakaichiRAG

# 依存関係をインストール
pip install -r requirements.txt
```

### 3. 環境設定

```bash
# .envファイルを作成
cp .env.example .env

# .envファイルを編集してOpenAI APIキーを設定
# OPENAI_API_KEY=your_openai_api_key_here
```

## 使い方

### 方法1: すべてを一度に実行

```bash
python main.py --all
```

これにより以下が実行されます：
1. ウェブサイトのスクレイピング
2. ドキュメントのインデックス作成
3. 対話型クエリモードの開始

### 方法2: 個別に実行

#### ステップ1: ウェブサイトをスクレイピング

```bash
python main.py --scrape
```

#### ステップ2: ドキュメントをインデックス

```bash
python main.py --index data/raw/scraped_data_*.json
```

#### ステップ3: 対話モードを開始

```bash
python main.py --chat
```

### 方法3: 単一クエリをテスト

```bash
python main.py --query "高市早苗の基本理念は何ですか？"
```

## プロジェクト構造

```
TakaichiRAG/
├── requirements.txt          # 依存関係
├── .env.example             # 環境変数テンプレート
├── .env                     # OpenAI APIキー（要作成、gitignore済み）
├── .gitignore               # Git除外ファイル設定
├── config.py                # 設定ファイル
├── scraper/                 # Webスクレイパーモジュール
│   ├── crawler.py          # クローラー実装
│   └── parser.py           # HTMLパーサー
├── data/                    # データディレクトリ
│   └── raw/               # スクレイピングした生データ（JSONファイル）
├── rag/                     # RAGモジュール
│   ├── setup.py           # RAGLite設定
│   ├── indexer.py         # ドキュメントインデクサー
│   └── query.py           # クエリエンジン
├── main.py                  # メインアプリケーション
├── test_rag.py             # RAGシステムテスト
├── test_crawler.py         # クローラーテスト
├── test_index.py           # インデックステスト
└── raglite.db              # RAGLiteデータベース（自動生成）
```

## テスト

システムが正しく動作しているか確認：

```bash
# RAGシステムのテスト
python test_rag.py

# クローラーのテスト
python test_crawler.py

# インデックスのテスト
python test_index.py
```

## 技術スタック

- **RAGフレームワーク**: [RAGLite](https://github.com/superlinear-ai/raglite)
- **LLM**: OpenAI GPT-4o-mini
- **Embeddings**: OpenAI text-embedding-3-large（日本語対応強化）
- **Reranker**: FlashRank ms-marco-MultiBERT-L-12（100+言語対応）
- **データベース**: DuckDB（ローカル、軽量、高速）
- **Webスクレイピング**: BeautifulSoup4 + requests

## トラブルシューティング

### OpenAI APIキーエラー

```
エラー: Please set OPENAI_API_KEY in .env file
```

解決策：
1. `.env`ファイルを作成: `cp .env.example .env`
2. `.env`ファイルにAPIキーを追加: `OPENAI_API_KEY=your_key_here`

### インポートエラー

```
ModuleNotFoundError: No module named 'raglite'
```

解決策：
```bash
pip install -r requirements.txt
```

### データベースが空

対話モードで回答が得られない場合：
1. まずスクレイピングを実行: `python main.py --scrape`
2. 次にインデックスを作成: `python main.py --index data/raw/scraped_data_*.json`

## 注意事項

- Webスクレイピングは適度な間隔で実行してください（サーバーへの負荷を考慮）
- OpenAI APIの使用には料金が発生します
- 収集したデータは個人利用の範囲でご使用ください

## 免責事項

- **データの正確性**: 本システムはWebスクレイピングとAI生成により情報を提供しますが、情報の正確性、完全性、最新性を保証するものではありません
- **公式情報の確認**: 重要な情報については必ず[高市早苗公式ウェブサイト](https://www.sanae.gr.jp/)で最新情報をご確認ください
- **AI生成コンテンツ**: RAGシステムの回答はAIにより生成されており、誤った情報や解釈を含む可能性があります
- **著作権**: 収集したコンテンツの著作権は元のウェブサイト運営者に帰属します。個人的な学習・研究目的以外での使用は避けてください
- **サーバー負荷**: 過度なスクレイピングはサーバーに負荷をかける可能性があります。適切な間隔を設けて実行してください
- **利用責任**: 本システムの利用により生じたいかなる損害についても、開発者は責任を負いません

## ライセンス

このプロジェクトは教育・研究目的で作成されています。商用利用は禁止されています。