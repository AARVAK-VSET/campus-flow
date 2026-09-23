from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.database import engine, Base, init_db
from backend.services.llm import AIServiceTimeoutError
from backend.routers import medical, stationery, announcements, parking, voice
import os
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)

AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_cache")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs when the server starts (not when this module is imported), so importing
    # the app - e.g. from a test - never creates the database file or audio folder.
    init_db()  # Create tables & indexes
    os.makedirs(AUDIO_DIR, exist_ok=True)
    yield


app = FastAPI(
    title="CampusFlow API",
    version="1.0.0",
    description="Intelligent Campus Task Automation API | AARVAK-VSET",
    lifespan=lifespan,
)


@app.exception_handler(AIServiceTimeoutError)
async def ai_service_timeout_handler(
    request: Request,
    exc: AIServiceTimeoutError,
):
    logger.warning(
        "External AI service timeout: %s %s | %s",
        request.method,
        request.url.path,
        str(exc),
    )
    return JSONResponse(
        status_code=504,
        content={
            "detail": str(exc),
        },
    )

# Logging Middleware
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.perf_counter()

    response = await call_next(request)

    duration = time.perf_counter() - start_time

    logger.info(
        "HTTP request: %s %s | status=%s | duration=%.4fs",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )

    return response

# CORS - Robust regex to allow any localhost/127.0.0.1 origin on any port
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check
@app.get("/api/health")
def health_check():
    try:
        return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Routes
app.include_router(medical.router)
app.include_router(stationery.router)
app.include_router(announcements.router)
app.include_router(parking.router)
app.include_router(voice.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to CampusFlow API | AARVAK-VSET", "status": "active"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)