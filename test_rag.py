#!/usr/bin/env python3
"""
Test script for the Takaichi RAG system.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import DEFAULT_RAG_CONFIG
from rag import QueryEngine


def test_basic_queries():
    """Test basic queries to the RAG system."""
    print("=" * 50)
    print("高市早苗RAGシステム - テスト")
    print("=" * 50)

    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ エラー: OPENAI_API_KEYが設定されていません。")
        print("   .envファイルを作成し、APIキーを設定してください。")
        print("   例: cp .env.example .env")
        print("       その後、.envファイルにAPIキーを追加してください。")
        return

    # Setup query engine
    try:
        config = DEFAULT_RAG_CONFIG
        query_engine = QueryEngine(config)
        print("✅ RAGシステムの初期化に成功しました。")
    except Exception as e:
        print(f"❌ 初期化エラー: {e}")
        return

    # Test queries
    test_questions = [
        "高市早苗の基本理念について教えてください。",
        "高市早苗の政治姿勢は何ですか？",
        "高市早苗の主な実績を教えてください。",
    ]

    print("\n" + "=" * 50)
    print("テストクエリ実行")
    print("=" * 50)

    for i, question in enumerate(test_questions, 1):
        print(f"\n【質問 {i}】{question}")
        print("-" * 30)

        try:
            answer = query_engine.query(question)
            if answer:
                print(f"【回答】\n{answer[:500]}...")  # Show first 500 chars
                print("✅ クエリ成功")
            else:
                print("⚠️ 回答が空です。データベースにドキュメントがインデックスされているか確認してください。")
        except Exception as e:
            print(f"❌ エラー: {e}")

    print("\n" + "=" * 50)
    print("テスト完了")
    print("=" * 50)


def check_environment():
    """Check if the environment is properly configured."""
    print("\n環境チェック:")
    print("-" * 30)

    # Check OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"✅ OpenAI API Key: 設定済み (****{api_key[-4:]})")
    else:
        print("❌ OpenAI API Key: 未設定")

    # Check database
    db_path = Path("raglite.db")
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"✅ Database: 存在します ({size_mb:.2f} MB)")
    else:
        print("⚠️ Database: 存在しません（データのインデックスが必要）")

    # Check data directories
    data_dir = Path("data")
    raw_dir = data_dir / "raw"
    if raw_dir.exists():
        json_files = list(raw_dir.glob("*.json"))
        print(f"✅ Raw data directory: {len(json_files)} JSONファイル")
    else:
        print("⚠️ Raw data directory: 存在しません")


if __name__ == "__main__":
    check_environment()

    # Only run tests if API key is set
    if os.getenv("OPENAI_API_KEY"):
        test_basic_queries()
    else:
        print("\nテストを実行するには、まずOpenAI APIキーを設定してください。")