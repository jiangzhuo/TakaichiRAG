#!/usr/bin/env python3
"""
Test indexing a small subset of documents.
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import DEFAULT_RAG_CONFIG
from rag import DocumentIndexer


def test_indexing():
    """Test indexing with a small subset of documents."""
    print("Testing RAGLite indexing...")
    print("-" * 40)

    # Load scraped data
    json_file = Path("data/raw/scraped_data_1759602591.json")
    with open(json_file, 'r', encoding='utf-8') as f:
        scraped_data = json.load(f)

    # Use only first 5 documents for testing
    test_data = scraped_data[:5]
    print(f"Testing with {len(test_data)} documents")

    # Initialize indexer
    indexer = DocumentIndexer(DEFAULT_RAG_CONFIG)

    # Index documents
    try:
        num_docs = indexer.index_scraped_data(test_data)
        print(f"\n✅ Successfully indexed {num_docs} documents!")

        # Show document titles
        print("\nIndexed documents:")
        for doc in test_data:
            print(f"  - {doc.get('title', 'No title')[:50]}...")

        return True
    except Exception as e:
        print(f"\n❌ Error during indexing: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_indexing()
    sys.exit(0 if success else 1)