"""Setup and configuration for RAGLite."""

import os
from pathlib import Path
from raglite import RAGLiteConfig
from rerankers import Reranker


def setup_raglite(
    db_path: str = "raglite.db",
    llm_model: str = "gpt-4o-mini",
    embedding_model: str = "text-embedding-3-large",
    api_key: str = None
) -> RAGLiteConfig:
    """
    Set up RAGLite with Japanese language support.

    Args:
        db_path: Path to the DuckDB database file
        llm_model: OpenAI model for generation (default: gpt-4o-mini)
        embedding_model: OpenAI embedding model (default: text-embedding-3-large)
        api_key: OpenAI API key (if not provided, reads from environment)

    Returns:
        RAGLiteConfig object configured for Japanese
    """
    # Get API key from environment if not provided
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")

    # Set OpenAI API key in environment for LiteLLM
    os.environ["OPENAI_API_KEY"] = api_key

    # Create configuration for Japanese language support
    config = RAGLiteConfig(
        # Database configuration
        db_url=f"duckdb:///{db_path}",

        # LLM configuration - using OpenAI models
        llm=llm_model,
        embedder=embedding_model,

        # Reranker configuration for Japanese
        # Using FlashRank with multilingual model (supports 100+ languages including Japanese)
        reranker=Reranker("ms-marco-MultiBERT-L-12", model_type="flashrank", verbose=0)
    )

    return config


def get_japanese_prompts():
    """
    Get Japanese language prompts for the RAG system.

    Returns:
        Dictionary of Japanese prompts
    """
    return {
        "system_prompt": (
            "あなたは高市早苗議員の公式ウェブサイトから収集された情報に基づいて回答する"
            "専門的なアシスタントです。以下の点に注意してください：\n"
            "1. 提供された文脈のみに基づいて回答すること\n"
            "2. 正確で事実に基づいた情報を提供すること\n"
            "3. 文脈に情報がない場合は、その旨を明確に伝えること\n"
            "4. 丁寧で分かりやすい日本語で回答すること"
        ),
        "context_prompt": "以下は関連する文脈情報です：\n{context}",
        "query_prompt": "質問：{query}\n\n上記の文脈に基づいて回答してください。",
        "no_context_response": (
            "申し訳ございません。お尋ねの内容に関する情報が、"
            "現在のデータベースには見つかりませんでした。"
        ),
    }


def validate_configuration(config: RAGLiteConfig) -> bool:
    """
    Validate the RAGLite configuration.

    Args:
        config: RAGLiteConfig object to validate

    Returns:
        True if configuration is valid
    """
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OpenAI API key not found")

    # Check if database is accessible
    db_url = config.db_url
    if db_url.startswith("duckdb://"):
        db_path = db_url.replace("duckdb:///", "")
        db_dir = Path(db_path).parent
        if not db_dir.exists():
            db_dir.mkdir(parents=True, exist_ok=True)

    return True