import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.api import api_router, admin_router, account_router
from app.models.user import async_session_maker
from app.core.processors.transaction_history import TransactionHistoryProcessor
from app.core.processors.transaction_history import set_transaction_history_processor
from app.core.scheduler import scheduler

from dotenv import load_dotenv

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load initial data from PostgreSQL to memory
    logger.info("Application startup: Loading data from PostgreSQL to memory")
    await scheduler.load_data_from_postgres()

    # Initialize database session and start background tasks
    db = async_session_maker()
    await scheduler.start()
    processor = TransactionHistoryProcessor(db)
    set_transaction_history_processor(processor)
    processor_task = asyncio.create_task(processor.start())

    yield

    # Cleanup on shutdown
    processor.stop()
    await processor_task
    await scheduler.stop()


BASE_DIR = Path(__file__).resolve().parent.parent.parent  # adjust if needed
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Full log file path
log_file = LOG_DIR / "backend.log"


class NginxStyleFormatter(logging.Formatter):
    def format(self, record):
        import os

        timestamp = self.formatTime(record, "%Y/%m/%d %H:%M:%S")
        level = record.levelname.lower()
        pid = os.getpid()
        return f"{timestamp} [{level}] {record.name} {pid}: {record.getMessage()}"


logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    filemode="a",
)
for handler in logging.getLogger().handlers:
    handler.setFormatter(NginxStyleFormatter())

logger = logging.getLogger(__name__)
logger.info("Main started")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix="/api")

app.include_router(account_router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    return {
        "status": "healthy",
        "service": "mailseller-api",
        "version": settings.VERSION,
    }
