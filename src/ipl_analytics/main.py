import time
import uuid
from fastapi import FastAPI,HTTPException,Depends,Request
from datetime import datetime, timezone
from ipl_analytics.db.session import get_connection
from ipl_analytics.api.v1.router import api_router
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
from fastapi.responses import JSONResponse

# Store IP -> list of request timestamps
request_history = defaultdict(list)
RATE_LIMIT = 60  # Max requests
WINDOW_SECONDS = 60  # In 60 seconds
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
        request_id  = request.headers.get("X-Request-ID") or str(uuid.uuid4())
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
        allow_origins=["*"],            # In development, allow all origins
        allow_credentials=True,
        allow_methods=["*"],            # Allow GET, POST, OPTIONS, etc.
        allow_headers=["*"],            # Allow all headers
    )
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
        # 1. Skip rate limiting for Swagger docs or health checks
        if request.url.path in ("/docs", "/redoc", "/openapi.json", "/health"):
            return await call_next(request)

        # 2. Get client IP address
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()

        # 3. Keep only timestamps within the last 60 seconds
        timestamps = [t for t in request_history[client_ip] if now - t < WINDOW_SECONDS]
        request_history[client_ip] = timestamps

        # 4. Check if limit exceeded
        if len(timestamps) >= RATE_LIMIT:
            retry_after = int(WINDOW_SECONDS - (now - timestamps[0]))
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded ({RATE_LIMIT} req/min). Try again in {max(1, retry_after)} seconds."
                },
                headers={"Retry-After": str(max(1, retry_after))}
            )

        # 5. Record this request and continue
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
            "/db-health": "Check the health of the database connection."
        }
    }
# Database connection dependency
@app.get("/db-health")
def db_health_check(db = Depends(get_connection)):
        try:
            result = db.execute("SELECT 1").fetchone()
            db.close()
            return {
                "database": "DuckDB",
                "status": "connected",
                "alive": result[0] == 1
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

@app.get("/health")
def health_check():
    return  {
      "status": "online",
      "environment": "development",
      "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    }
