"""FastAPI web server for Takaichi RAG chat interface."""

import sys
from pathlib import Path
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import DEFAULT_RAG_CONFIG
from rag import QueryEngine


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    num_chunks: int = 5


class HealthResponse(BaseModel):
    status: str
    version: str


# Initialize FastAPI app
app = FastAPI(
    title="たかいち RAG Chat API",
    description="たかいちRAGシステムのWebチャットインターフェース",
    version="1.0.0"
)

# Mount static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Initialize query engine
query_engine = QueryEngine(DEFAULT_RAG_CONFIG)


@app.get("/", response_class=FileResponse)
async def read_root():
    """Serve the main chat interface."""
    index_path = static_dir / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Chat interface not found")
    return FileResponse(index_path)


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="1.0.0")


@app.post("/api/chat")
async def chat_stream(request: ChatRequest):
    """
    Stream chat responses with sources.

    Returns Server-Sent Events (SSE) stream with:
    - answer chunks (streaming)
    - sources (after answer completion)
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    async def generate_response() -> AsyncGenerator[str, None]:
        try:
            # Get answer with sources
            result = query_engine.query_with_sources(
                question=request.message,
                num_chunks=request.num_chunks
            )

            # Stream answer character by character for better UX
            answer = result["answer"]
            for i in range(0, len(answer), 10):  # Send in chunks of 10 chars
                chunk = answer[i:i+10]
                yield f"data: {json.dumps({'type': 'answer', 'content': chunk})}\n\n"

            # Send end of answer marker
            yield f"data: {json.dumps({'type': 'answer_end'})}\n\n"

            # Send sources
            if result["sources"]:
                yield f"data: {json.dumps({'type': 'sources', 'content': result['sources']})}\n\n"

            # Send completion marker
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            error_msg = f"エラーが発生しました: {str(e)}"
            yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"

    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """
    Run the web server.

    Args:
        host: Host address to bind to
        port: Port number to listen on
    """
    import uvicorn

    print("=" * 50)
    print("たかいち RAG Webチャットサーバー")
    print("=" * 50)
    print(f"\n🌐 サーバー起動中: http://{host}:{port}")
    print(f"📱 ブラウザで以下にアクセス: http://localhost:{port}")
    print("\n⚠️  免責事項: 本システムは非公式の研究プロジェクトであり、特定の政治家や組織とは一切関係ありません")
    print("Ctrl+C でサーバーを停止\n")

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()
