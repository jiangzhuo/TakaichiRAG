"""Document indexer for RAGLite."""

import json
from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm
from raglite import Document, insert_documents, RAGLiteConfig


class DocumentIndexer:
    """Indexer for processing and storing documents in RAGLite."""

    def __init__(self, config: RAGLiteConfig):
        """
        Initialize the document indexer.

        Args:
            config: RAGLite configuration
        """
        self.config = config

    def index_scraped_data(self, scraped_data: List[Dict]) -> int:
        """
        Index scraped data into RAGLite.

        Args:
            scraped_data: List of scraped data dictionaries

        Returns:
            Number of documents indexed
        """
        documents = []

        print(f"Processing {len(scraped_data)} scraped pages...")

        for data in tqdm(scraped_data, desc="Creating documents"):
            # Create document from scraped data
            doc = self._create_document_from_scraped(data)
            if doc:
                documents.append(doc)

        if documents:
            print(f"Indexing {len(documents)} documents...")
            insert_documents(documents, config=self.config)
            print(f"Successfully indexed {len(documents)} documents.")
        else:
            print("No documents to index.")

        return len(documents)

    def index_json_file(self, json_path: Path) -> int:
        """
        Index documents from a JSON file.

        Args:
            json_path: Path to the JSON file containing scraped data

        Returns:
            Number of documents indexed
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            scraped_data = json.load(f)

        return self.index_scraped_data(scraped_data)

    def _create_document_from_scraped(self, data: Dict) -> Optional[Document]:
        """
        Create a RAGLite Document from scraped data.

        Args:
            data: Scraped data dictionary

        Returns:
            Document object or None if content is insufficient
        """
        # Skip if content is too short
        if not data.get('content') or len(data['content']) < 100:
            return None

        # Prepare document content
        content = self._format_document_content(data)

        # Create metadata
        metadata = {
            'url': data.get('url', ''),
            'title': data.get('title', ''),
            'category': data.get('category', 'general'),
            'word_count': data.get('word_count', 0),
        }

        # Add description if available
        if data.get('description'):
            metadata['description'] = data['description']

        # Create document using from_text method which handles initialization properly
        # Use ** to unpack metadata dict as keyword arguments
        doc = Document.from_text(
            content,
            **metadata
        )

        return doc

    def _format_document_content(self, data: Dict) -> str:
        """
        Format the document content for indexing.

        Note: Title and URL are stored in metadata only to avoid redundancy.
        Only category is included in content as it improves search context.

        Args:
            data: Scraped data dictionary

        Returns:
            Formatted content string
        """
        parts = []

        # Add category only (provides search context, stored in metadata too)
        category_labels = {
            'idea': '基本理念',
            'posture': '政治姿勢',
            'results': '実績',
            'kaiken': '記者会見',
            'column': 'コラム',
        }
        category = category_labels.get(data.get('category', ''), data.get('category', ''))
        parts.append(f"[{category}]")

        # Add main content
        parts.append(data['content'])

        return "\n".join(parts)

    def add_single_document(self, text: str, metadata: Dict = None) -> bool:
        """
        Add a single document to the index.

        Args:
            text: Document text
            metadata: Optional metadata dictionary

        Returns:
            True if successful
        """
        try:
            doc = Document(
                content=text,  # Use 'content' field instead of 'text'
                metadata=metadata or {}
            )
            insert_documents([doc], config=self.config)
            return True
        except Exception as e:
            print(f"Error adding document: {e}")
            return False

    def bulk_add_documents(self, documents: List[Dict]) -> int:
        """
        Bulk add documents to the index.

        Args:
            documents: List of document dictionaries with 'text'/'content' and optional 'metadata'

        Returns:
            Number of documents added
        """
        docs = []
        for doc_data in documents:
            # Support both 'text' and 'content' field names for backward compatibility
            content = doc_data.get('content') or doc_data.get('text')
            if content:
                doc = Document(
                    content=content,  # Use 'content' field
                    metadata=doc_data.get('metadata', {})
                )
                docs.append(doc)

        if docs:
            insert_documents(docs, config=self.config)

        return len(docs)