import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
import app.database.base  # noqa: F401 — registers all ORM models at startup
from app.routes import auth_routes, elderly_routes, caregiver_routes, healthcare_routes, checkin_routes

logger = logging.getLogger(__name__)


def get_allowed_origins() -> list[str]:
    return [
        origin.strip().rstrip("/")
        for origin in settings.FRONTEND_URL.split(",")
        if origin.strip()
    ]


def _warmup_rag() -> None:
    """Muat model embedding dan FAISS index di thread terpisah saat startup."""
    try:
        from app.services.rag_guidance_service import _load_resources
        _load_resources()
        logger.info("Model RAG berhasil dimuat saat startup.")
    except Exception as exc:
        logger.warning("Pemanasan model RAG gagal; layanan tetap berjalan. Detail: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as pool:
        loop.run_in_executor(pool, _warmup_rag)
    yield
    logger.info("Shutting down TIARA API")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "TIARA — AI-Powered Cognitive Decline Screening & Caregiver Support Platform. "
        "⚕️ Not a medical diagnosis tool. Informational use only."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_origin_regex=r"^https://(www\.)?tiaracare\.my\.id$|^http://localhost(:\d+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Dashboard-Token"],
)

# ── API Routes ─────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(auth_routes.router, prefix=API_PREFIX)
app.include_router(elderly_routes.router, prefix=API_PREFIX)
app.include_router(caregiver_routes.router, prefix=API_PREFIX)
app.include_router(healthcare_routes.router, prefix=API_PREFIX)
app.include_router(checkin_routes.router, prefix=API_PREFIX)


# ── Health check ───────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for Docker and load balancer probes."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "Welcome to TIARA API",
        "docs": "/docs",
        "version": settings.APP_VERSION,
    }
