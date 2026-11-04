import time
import uuid
from collections import defaultdict
from datetime import UTC, datetime

import duckdb
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ipl_analytics.api.dependencies import get_db
from ipl_analytics.api.v1.router import api_router

# Store IP -> list of request timestamps (typed for mypy)
request_history: dict[str, list[float]] = defaultdict(list)
last_cleanup_time: float = time.time()
RATE_LIMIT = 60  # Max requests
WINDOW_SECONDS = 60  # In 60 seconds
CLEANUP_INTERVAL = 60.0  # Prune dead IPs every 60 seconds


def get_client_ip(request: Request) -> str:
    """Extract real client IP behind reverse proxies (Render, Nginx, Cloudflare) or socket host."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    return request.client.host if request.client else "127.0.0.1"


app = FastAPI()


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{duration:.4f}s"
    return response


@app.middleware("http")
async def add_request_id_header(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In development, allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow GET, POST, OPTIONS, etc.
    allow_headers=["*"],  # Allow all headers
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    global last_cleanup_time

    # 1. Skip rate limiting for Swagger docs, root, and health checks
    if request.url.path in (
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/db-health",
        "/",
    ):
        return await call_next(request)

    # 2. Get client IP address (proxy-aware)
    client_ip = get_client_ip(request)
    now = time.time()

    # 3. Periodic memory cleanup to prevent unbounded dict growth (OOM protection)
    if now - last_cleanup_time > CLEANUP_INTERVAL:
        stale_ips = [
            ip
            for ip, timestamps in request_history.items()
            if not timestamps or (now - timestamps[-1] >= WINDOW_SECONDS)
        ]
        for ip in stale_ips:
            del request_history[ip]
        last_cleanup_time = now

    # 4. Keep only timestamps within the last 60 seconds for the active client
    timestamps = [t for t in request_history[client_ip] if now - t < WINDOW_SECONDS]
    request_history[client_ip] = timestamps

    # 5. Check if limit exceeded
    if len(timestamps) >= RATE_LIMIT:
        retry_after = int(WINDOW_SECONDS - (now - timestamps[0]))
        return JSONResponse(
            status_code=429,
            content={
                "detail": (
                    f"Rate limit exceeded ({RATE_LIMIT} req/min). "
                    f"Try again in {max(1, retry_after)} seconds."
                )
            },
            headers={"Retry-After": str(max(1, retry_after))},
        )

    # 6. Record this request and continue
    request_history[client_ip].append(now)
    response = await call_next(request)
    return response


app.include_router(api_router, prefix="/api/v1")


# Home route returns my project name and description
@app.get("/")
def home():
    return {
        "project": "IPL Analytics",
        "description": "A project to analyze IPL data using FastAPI and DuckDB.",
        "Author": "Mohd Hamza",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Check the health of the application.",
            "/db-health": "Check the health of the database connection.",
        },
    }


# Database connection dependency with guaranteed cleanup via get_db
@app.get("/db-health")
def db_health_check(db: duckdb.DuckDBPyConnection = Depends(get_db)):
    result = db.execute("SELECT 1").fetchone()
    return {
        "database": "DuckDB",
        "status": "connected",
        "alive": result is not None and result[0] == 1,
    }


@app.get("/health")
def health_check():
    return {
        "status": "online",
        "environment": "development",
        "version": "1.0.0",
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
