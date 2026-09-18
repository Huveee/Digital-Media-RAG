from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from Security.userdatabase import engine, SessionLocal as UserSessionLocal
from Security.frontend_verification import verify_frontend
from typing import Annotated, List, Optional, Literal
import json
import time
import uuid
import os
from dotenv import load_dotenv
from Core.bot_selection import generate_answer, generate_answer_stream
from Core.chat_history import save_user_message, save_assistant_message, get_chat_history
from Core.runtime_config import RuntimeConfig

from Security.dbBase import Base
from fastapi.responses import FileResponse
import sys

load_dotenv()

print("=== Database Initialization ===")
print(f"DATABASE_PATH env: {os.getenv('DATABASE_PATH')}")
print(f"DATABASE_URL env: {os.getenv('DATABASE_URL')}")

try:
    from Security.userdatabase import SQLALCHEMY_DATABASE_URL
    print(f"Using database URL: {SQLALCHEMY_DATABASE_URL}")
    
    # Check if storage directory exists
    db_path = os.getenv('DATABASE_PATH')
    if db_path:
        storage_dir = os.path.dirname(db_path)
        print(f"Storage directory: {storage_dir}")
        print(f"Storage directory exists: {os.path.exists(storage_dir)}")
        if os.path.exists(storage_dir):
            print(f"Storage directory is writable: {os.access(storage_dir, os.W_OK)}")
    
    print("Creating tables...")
    Base.metadata.create_all(bind=engine, checkfirst=True)
    print("✓ Tables created successfully!")
except Exception as e:
    print(f"✗ ERROR creating tables: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=== Initialization Complete ===")


# Initialize FastAPI app
app = FastAPI()
#app.include_router(auth.routerauth)
#router = APIRouter(prefix="/chats", tags=["Chats"])


# Enable CORS - read allowed origins from environment
allowed_origins_env = os.getenv("FRONTEND_ALLOWED_ORIGINS", "http://localhost:3000")
ALLOWED_ORIGINS = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Get UserDatabase session
def getUserDatabase():
    userdb = UserSessionLocal()
    try:
        yield userdb
    finally:
        userdb.close()

userdb_dependency = Annotated[Session, Depends(getUserDatabase)]

"""
# Define a request schema
class ChatRequest(BaseModel):
    chat_id: str
    prompt: str
   # lang: str = 'de' # or 'en'

class FrontendConfigRequest(BaseModel):
    active_bot: Optional[str] = None
    variation_enabled: Optional[bool] = None
    variation_type: Optional[str] = None
    varllm_style: Optional[str] = None
    llm_model_name: Optional[str] = None
    varllm_model_name: Optional[str] = None
    language: Optional[str] = None
"""

class OpenAIChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

# Used for OpenAI-Compatible Endpoint
class ChatCompletionRequest(BaseModel):
    chat_id: str
    messages: List[OpenAIChatMessage]
    stream: Optional[bool] = True
    image: Optional[str] = None  # base64-encoded image; triggers mistral-large-instruct
    # Inline config (use defaults if not provided)
    active_bot: str = "llm"
    variation_enabled: bool = False
    variation_type: str = "metaphor"
    varllm_style: str = "board"
    llm_model_name: str = "meta-llama-3.1-8b-instruct"
    varllm_model_name: str = "meta-llama-3.1-8b-instruct"
    language: str = "de"


"""
@app.post("/initialize_config")
async def update_config(
    cfg: FrontendConfigRequest,
    verified = Depends(verify_frontend)
):
    


    return {
        "status": "success",
        "message": "Configuration updated",
    }
"""
# ============================================================================
# OpenAI-Compatible Endpoint for Frontend Integration
# Compatible with Vercel AI SDK and standard OpenAI clients.
# ============================================================================



@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest, db: Session = Depends(getUserDatabase), verified = Depends(verify_frontend)):
    try:
        # Build config from request body instead of global singleton
        config = RuntimeConfig(
        active_bot=req.active_bot,
        variation_enabled=req.variation_enabled,
        variation_type=req.variation_type,
        varllm_style=req.varllm_style,
        llm_model_name=req.llm_model_name,
        varllm_model_name=req.varllm_model_name,
        language=req.language,
        )

        # When an image is provided, force the vision-capable model
        if req.image:
            config.active_bot = "llm"
            config.llm_model_name = "mistral-large-instruct"

        # 1. Save the User message (with image if present)
        save_user_message(db, req.chat_id, req.messages[-1].content, image=req.image)

        # 2. Build context from chat history
        history = get_chat_history(db, req.chat_id)
        context_parts = []
        for m in history:
            line = f"{m.sender}: {m.content}"
            if getattr(m, "image", None):
                line += " [image attached]"
            context_parts.append(line)
        context = "\n".join(context_parts)

        final_prompt = f"{context}\nassistant:"  # History already includes the saved user message

        
        # Handle streaming
        if req.stream:
            async def generate_stream():
                chunk_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
                collected_answer = []

                # Stream tokens directly from the LLM as they arrive
                for token in generate_answer_stream(final_prompt, config, image=req.image):
                    token = token.replace('\\n', '\n')
                    collected_answer.append(token)

                    chunk_data = {
                        "id": chunk_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "choices": [{
                            "index": 0,
                            "delta": {"content": token},
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"

                # Save the complete answer to the database after streaming
                full_answer = "".join(collected_answer)
                save_assistant_message(db, req.chat_id, full_answer)

                final_chunk = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "choices": [{
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }]
                }
                yield f"data: {json.dumps(final_chunk)}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            # Non-streaming response
            # 3. bot_selection generates answer
            answer = generate_answer(final_prompt, config, image=req.image)
            answer = answer.replace('\\n', '\n')

            # 4. Save the assistant message
            save_assistant_message(db, req.chat_id, answer)

            return {
                "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                "object": "chat.completion",
                "created": int(time.time()),
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": answer,
                    },
                    "finish_reason": "stop"
                }]
            }
    except Exception as e:
        print(f"[/v1/chat/completions] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Chat Management Endpoints
# ============================================================================

@app.delete("/v1/chat/{chat_id}")
async def delete_chat(chat_id: str, db: Session = Depends(getUserDatabase), verified = Depends(verify_frontend)):
    """Delete all messages for a given chat session."""
    from Security.BaseModels import ChatMessage
    deleted = db.query(ChatMessage).filter(ChatMessage.chat_id == chat_id).delete()
    db.commit()
    return {"deleted": deleted}


# ============================================================================
# Admin / Debug Endpoints — protected by X-Frontend-Key
# ============================================================================

@app.get("/admin/db/download")
def admin_download_db(request: Request):
    """Download the raw SQLite database file.
    Auth: pass X-Frontend-Key header (API calls only).
    """
    from Security.frontend_verification import FRONTEND_SECRET
    provided = request.headers.get("x-frontend-key")
    if not provided or provided != FRONTEND_SECRET:
        raise HTTPException(status_code=401, detail="Invalid key")
    db_path = os.getenv("DATABASE_PATH", "/tmp/chat_history_database.db")
    if not os.path.isfile(db_path):
        raise HTTPException(status_code=404, detail=f"Database file not found at {db_path}")
    return FileResponse(
        path=db_path,
        media_type="application/octet-stream",
        filename="chat_history_v2.db",
    )



