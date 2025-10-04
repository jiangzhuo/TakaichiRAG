"""Query engine for RAGLite."""

from typing import List, Dict, Optional, Generator
from raglite import rag, RAGLiteConfig, retrieve_context, add_context


class QueryEngine:
    """Query engine for searching and generating answers."""

    def __init__(self, config: RAGLiteConfig):
        """
        Initialize the query engine.

        Args:
            config: RAGLite configuration
        """
        self.config = config

    def query(self, question: str, stream: bool = False) -> str:
        """
        Query the RAG system with a question.

        Args:
            question: The question to ask
            stream: Whether to stream the response

        Returns:
            The generated answer
        """
        # Create messages in OpenAI format
        messages = [
            {
                "role": "system",
                "content": (
                    "あなたは高市早苗議員に関する情報を提供する専門的なアシスタントです。"
                    "提供された文脈情報のみに基づいて、正確で詳細な日本語の回答を提供してください。"
                )
            },
            {
                "role": "user",
                "content": question
            }
        ]

        # Get response from RAG
        if stream:
            return self._stream_response(messages)
        else:
            response_stream = rag(messages, config=self.config)
            full_response = ""
            for chunk in response_stream:
                if chunk:
                    full_response += chunk
            return full_response

    def _stream_response(self, messages: List[Dict]) -> Generator[str, None, None]:
        """
        Stream the response from RAG.

        Args:
            messages: Messages in OpenAI format

        Yields:
            Response chunks
        """
        response_stream = rag(messages, config=self.config)
        for chunk in response_stream:
            if chunk:
                yield chunk

    def query_with_context(self, question: str, max_context: int = 3) -> Dict:
        """
        Query with explicit context retrieval.

        Args:
            question: The question to ask
            max_context: Maximum number of context documents to retrieve

        Returns:
            Dictionary with answer and source documents
        """
        # This is a simplified version - RAGLite handles context internally
        # For more control, you might need to use lower-level APIs

        answer = self.query(question, stream=False)

        return {
            "question": question,
            "answer": answer,
            "sources": []  # RAGLite handles sources internally
        }

    def batch_query(self, questions: List[str]) -> List[Dict]:
        """
        Process multiple questions in batch.

        Args:
            questions: List of questions

        Returns:
            List of answer dictionaries
        """
        results = []

        for question in questions:
            result = self.query_with_context(question)
            results.append(result)

        return results

    def query_with_sources(self, question: str, num_chunks: int = 5) -> Dict:
        """
        Query the RAG system and return answer with source citations.

        Args:
            question: The question to ask
            num_chunks: Number of chunks to retrieve (default: 5)

        Returns:
            Dictionary containing:
                - question: Original question
                - answer: Generated answer
                - sources: List of source documents with metadata
                - num_sources: Number of sources
        """
        # 1. Retrieve context using RAGLite's high-level API
        chunk_spans = retrieve_context(
            query=question,
            num_chunks=num_chunks,
            config=self.config
        )

        # 2. Add context to create RAG instruction
        messages = [add_context(user_prompt=question, context=chunk_spans)]

        # 3. Generate answer
        stream = rag(messages, config=self.config)
        answer = "".join(chunk for chunk in stream if chunk)

        # 4. Extract source information from chunk_spans
        sources = []
        for i, chunk_span in enumerate(chunk_spans, 1):
            source = {
                "index": i,
                "document_id": chunk_span.document.id,
                "url": chunk_span.document.url or chunk_span.document.filename,
                "title": chunk_span.document.metadata_.get('title', 'N/A'),
                "category": chunk_span.document.metadata_.get('category', 'general'),
                "chunk_range": f"{chunk_span.chunks[0].id} → {chunk_span.chunks[-1].id}",
                "content": chunk_span.content[:200] + "..." if len(chunk_span.content) > 200 else chunk_span.content,
                "full_content": chunk_span.content
            }
            sources.append(source)

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "num_sources": len(sources)
        }

    @staticmethod
    def _format_source(chunk_span, index: int) -> str:
        """
        Format a ChunkSpan as a readable Japanese citation.

        Args:
            chunk_span: ChunkSpan object containing document and chunk information
            index: Citation index number

        Returns:
            Formatted citation string in Japanese
        """
        # Get document metadata
        doc = chunk_span.document
        title = doc.metadata_.get('title', 'N/A')
        category = doc.metadata_.get('category', 'general')
        url = doc.url or doc.filename

        # Category labels in Japanese
        category_labels = {
            'idea': '基本理念',
            'posture': '政治姿勢',
            'results': '実績',
            'kaiken': '記者会見',
            'column': 'コラム',
        }
        category_jp = category_labels.get(category, category)

        # Format content preview (first 100 characters)
        content_preview = chunk_span.content[:100].replace('\n', ' ')
        if len(chunk_span.content) > 100:
            content_preview += "..."

        # Format citation
        citation = f"[{index}] {title} ({category_jp})\n"
        citation += f"    出典: {url}\n"
        citation += f"    内容: {content_preview}"

        return citation

    def interactive_query(self):
        """
        Run an interactive query session with source citations.
        """
        print("\n高市早苗RAGシステムへようこそ！")
        print("質問を入力してください（終了するには 'quit' または 'exit' を入力）\n")

        while True:
            try:
                # Get user input
                question = input("質問: ").strip()

                # Check for exit commands
                if question.lower() in ['quit', 'exit', '終了', 'やめる']:
                    print("\nセッションを終了します。ありがとうございました！")
                    break

                # Skip empty questions
                if not question:
                    continue

                print("\n回答を生成中...\n")

                # Retrieve context using RAGLite's high-level API
                chunk_spans = retrieve_context(
                    query=question,
                    num_chunks=5,
                    config=self.config
                )

                # Add context to create RAG instruction
                messages = [add_context(user_prompt=question, context=chunk_spans)]

                # Stream the response
                print("回答: ", end="", flush=True)
                stream = rag(messages, config=self.config)
                for chunk in stream:
                    if chunk:
                        print(chunk, end="", flush=True)

                # Display source citations
                if chunk_spans:
                    print("\n\n【参考資料】\n")
                    for i, chunk_span in enumerate(chunk_spans, 1):
                        citation = self._format_source(chunk_span, i)
                        print(citation + "\n")

                print("="*50 + "\n")

            except KeyboardInterrupt:
                print("\n\nセッションを終了します。")
                break
            except Exception as e:
                print(f"\nエラーが発生しました: {e}")
                print("もう一度お試しください。\n")