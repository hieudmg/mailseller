import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.api import api_router, admin_router, account_router
from app.models.user import UserRead, UserCreate, UserUpdate, async_session_maker
from app.core.processors.transaction_history import TransactionHistoryProcessor
from app.core.processors.transaction_history import set_transaction_history_processor
from app.users import web_auth_backend, fastapi_users
from app.core.redis_manager import redis_manager
from app.core.scheduler import scheduler

from dotenv import load_dotenv

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_manager.connect()
    await redis_manager.load_lua_scripts()
    await scheduler.start()
    db = async_session_maker()
    processor = TransactionHistoryProcessor(db)
    set_transaction_history_processor(processor)
    processor_task = asyncio.create_task(processor.start())

    yield

    processor.stop()
    await processor_task
    await scheduler.stop()
    await redis_manager.disconnect()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
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

app.include_router(
    account_router, prefix="/api"
)

@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    return {
        "status": "healthy",
        "service": "mailseller-api",
        "version": settings.VERSION
    }
