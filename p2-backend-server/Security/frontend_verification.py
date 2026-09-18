import os
from fastapi import Header, HTTPException, Request
from dotenv import load_dotenv

load_dotenv()
FRONTEND_SECRET = os.getenv("FRONTEND_SECRET_KEY", "")

# Load allowed origins from .env
allowed_origins_env = os.getenv("FRONTEND_ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS = set(o.strip() for o in allowed_origins_env.split(",") if o.strip())


async def verify_frontend(
    request: Request,
    x_frontend_key: str | None = Header(None),
    origin: str | None = Header(None),      # <-- Comes automatically from Browser
):
    # 1. Check key
    if not x_frontend_key or x_frontend_key != FRONTEND_SECRET:
        raise HTTPException(status_code=401, detail="Invalid frontend key")

    # 2. Check allowed origin (browser will send it)
    if origin not in ALLOWED_ORIGINS:
        raise HTTPException(status_code=403, detail=f"Origin {origin} not allowed")

    return True


"""
import os
import hmac
import hashlib
import time
from fastapi import Header, HTTPException, Request
from dotenv import load_dotenv
load_dotenv()

FRONTEND_SECRET = os.getenv("FRONTEND_SECRET_KEY", "")
MAX_AGE_SECONDS = 60
ALLOWED_ORIGINS = {
    "http://localhost:3000",
    "http://localhost:8000",
    "https://production-frontend.example.com", # <-- Replace with your actual production URL
}


def safe_compare(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)


async def verify_frontend(request: Request,
                          x_frontend_key: str | None = Header(None),
                          x_frontend_timestamp: str | None = Header(None),
                          x_frontend_signature: str | None = Header(None),
                          x_forwarded_origin: str | None = Header(None)):
    # 1. Check key
    if not x_frontend_key or x_frontend_key != FRONTEND_SECRET:
        raise HTTPException(status_code=401, detail="Invalid frontend key")

    # 2. Check Origin (optional but recommended)
    origin = x_forwarded_origin or request.headers.get("origin")
    if origin not in ALLOWED_ORIGINS:
        raise HTTPException(status_code=401, detail="Origin not allowed")

    # 3. Timestamp check (replay prevention)
    try:
        ts = int(x_frontend_timestamp)
    except:
        raise HTTPException(status_code=401, detail="Invalid timestamp")

    now = int(time.time())
    if abs(now - ts) > MAX_AGE_SECONDS:
        raise HTTPException(status_code=401, detail="Stale request (replay detected)")

    # 4. Rebuild message
    message = f"{request.method}|{request.url.path}|{x_frontend_timestamp}".encode()

    # 5. Compute signature
    computed = hmac.new(
        FRONTEND_SECRET.encode(),
        message,
        hashlib.sha256
    ).hexdigest()

    # 6. Compare signatures in constant time
    if not safe_compare(computed, x_frontend_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    return True"""