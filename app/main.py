from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.database.database import init_db
from app.utils.logging import setup_logging, logger
from app.api.routes.chat import router as chat_router
from app.api.routes.conversations import router as conversations_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize logging and database schema on startup
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME}...")
    await init_db()
    yield
    logger.info("Shutting down application...")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered Indian Stock Market Research Assistant backed by Gemini LLM & Tapetide MCP.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(chat_router)
app.include_router(conversations_router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "llm_provider": settings.LLM_PROVIDER,
        "mcp_provider": settings.MCP_PROVIDER,
        "database": settings.DATABASE_URL.split("://")[0]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
