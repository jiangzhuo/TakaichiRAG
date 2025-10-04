"""Configuration for the Takaichi RAG system."""

import os
from pathlib import Path
from dotenv import load_dotenv
from raglite import RAGLiteConfig
from rerankers import Reranker

# Load environment variables
load_dotenv()

# Project paths
BASE_DIR = Path(__file__).parent.absolute()
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Create directories if they don't exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Please set OPENAI_API_KEY in .env file")

# Set OpenAI API key in environment for LiteLLM
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# RAGLite configuration with Japanese language support
DEFAULT_RAG_CONFIG = RAGLiteConfig(
    # Database configuration (using local DuckDB)
    db_url=os.getenv("DB_URL", "duckdb:///raglite.db"),

    # OpenAI models (with Japanese support)
    llm=os.getenv("LLM_MODEL", "gpt-4o-mini"),
    embedder=os.getenv("EMBEDDING_MODEL", "text-embedding-3-large"),

    # Reranker configuration for Japanese
    # Using ms-marco-MultiBERT-L-12 for multilingual support (100+ languages including Japanese)
    reranker=Reranker("ms-marco-MultiBERT-L-12", model_type="flashrank", verbose=0)
)

# Scraper configuration
SCRAPER_CONFIG = {
    "base_url": "https://www.sanae.gr.jp",
    "target_pages": {
        "idea": "idea.html",           # 基本理念
        "posture": "posture.html",     # 政治姿勢
        "results": "results.html",     # 実績
        "kaiken": "kaiken.html",       # 記者会見
        "column": "column.html",       # コラム
    },
    "headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
    },
    "timeout": 30,
    "delay_between_requests": 1.0,  # Be polite to the server
}