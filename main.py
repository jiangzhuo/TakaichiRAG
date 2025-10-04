#!/usr/bin/env python3
"""
高市早苗 RAGシステム - メインアプリケーション

This application scrapes content from Sanae Takaichi's official website
and creates a RAG (Retrieval-Augmented Generation) system for Q&A.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import DEFAULT_RAG_CONFIG, SCRAPER_CONFIG, RAW_DATA_DIR, PROCESSED_DATA_DIR
from scraper import WebCrawler
from rag import setup_raglite, DocumentIndexer, QueryEngine


def scrape_website(output_file: Optional[Path] = None) -> Path:
    """
    Scrape content from Sanae's website.

    Args:
        output_file: Optional path to save scraped data

    Returns:
        Path to the saved JSON file
    """
    print("=" * 50)
    print("高市早苗ウェブサイトスクレイピング開始")
    print("=" * 50)

    # Initialize crawler
    crawler = WebCrawler(SCRAPER_CONFIG, RAW_DATA_DIR)

    # Crawl all pages
    scraped_data = crawler.crawl_all_pages()

    # Save data
    output_path = crawler.save_data(output_file)

    print(f"\nスクレイピング完了！")
    print(f"収集ページ数: {len(scraped_data)}")
    print(f"保存先: {output_path}")

    return output_path


def index_documents(json_file: Path) -> int:
    """
    Index scraped documents into RAGLite.

    Args:
        json_file: Path to JSON file containing scraped data

    Returns:
        Number of documents indexed
    """
    print("\n" + "=" * 50)
    print("ドキュメントインデックス作成開始")
    print("=" * 50)

    # Setup RAGLite with Japanese configuration
    config = DEFAULT_RAG_CONFIG

    # Initialize indexer
    indexer = DocumentIndexer(config)

    # Index documents
    num_docs = indexer.index_json_file(json_file)

    print(f"\nインデックス作成完了！")
    print(f"インデックス済みドキュメント数: {num_docs}")

    return num_docs


def run_interactive_query():
    """
    Run interactive query session.
    """
    print("\n" + "=" * 50)
    print("高市早苗RAGシステム - インタラクティブモード")
    print("=" * 50)

    # Setup RAGLite
    config = DEFAULT_RAG_CONFIG

    # Initialize query engine
    query_engine = QueryEngine(config)

    # Run interactive session
    query_engine.interactive_query()


def test_query(question: str):
    """
    Test a single query.

    Args:
        question: The question to test
    """
    # Setup RAGLite
    config = DEFAULT_RAG_CONFIG

    # Initialize query engine
    query_engine = QueryEngine(config)

    print(f"\n質問: {question}")
    print("\n回答を生成中...\n")

    # Get answer
    answer = query_engine.query(question)

    print(f"回答:\n{answer}")


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="高市早苗RAGシステム - Webスクレイピング & 質問応答",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # すべての処理を実行（スクレイピング → インデックス作成 → 対話モード）
  python main.py --all

  # ウェブサイトをスクレイピングのみ
  python main.py --scrape

  # 既存のJSONファイルからインデックス作成
  python main.py --index data/raw/scraped_data.json

  # 対話モードを開始（CLI）
  python main.py --chat

  # Webチャットインターフェースを起動
  python main.py --web

  # 単一の質問をテスト
  python main.py --query "高市早苗の基本理念は何ですか？"
        """
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='すべての処理を実行（スクレイピング、インデックス作成、対話モード）'
    )
    parser.add_argument(
        '--scrape',
        action='store_true',
        help='ウェブサイトをスクレイピング'
    )
    parser.add_argument(
        '--index',
        type=str,
        metavar='JSON_FILE',
        help='JSONファイルからドキュメントをインデックス'
    )
    parser.add_argument(
        '--chat',
        action='store_true',
        help='対話型クエリモードを開始'
    )
    parser.add_argument(
        '--query',
        type=str,
        metavar='QUESTION',
        help='単一の質問をテスト'
    )
    parser.add_argument(
        '--web',
        action='store_true',
        help='Webチャットインターフェースを起動'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Webサーバーのホストアドレス（デフォルト: 0.0.0.0）'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Webサーバーのポート番号（デフォルト: 8000）'
    )

    args = parser.parse_args()

    # If no arguments provided, show help
    if not any(vars(args).values()):
        parser.print_help()
        return

    try:
        json_file = None

        # Execute all steps
        if args.all:
            json_file = scrape_website()
            index_documents(json_file)
            run_interactive_query()

        # Execute individual steps
        else:
            if args.scrape:
                json_file = scrape_website()

            if args.index:
                json_file = Path(args.index)
                if not json_file.exists():
                    print(f"エラー: ファイルが見つかりません: {json_file}")
                    sys.exit(1)
                index_documents(json_file)

            if args.chat:
                run_interactive_query()

            if args.query:
                test_query(args.query)

            if args.web:
                from web_api import run_server
                run_server(host=args.host, port=args.port)

    except KeyboardInterrupt:
        print("\n\n処理を中断しました。")
        sys.exit(0)
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
