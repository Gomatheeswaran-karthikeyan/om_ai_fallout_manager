from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.fallout import router as fallout_router
from app.config.settings import settings
from app.db.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _warmup()
    yield
    await engine.dispose()


async def _warmup():
    """Pre-load the LLM model and DB pool before the first request."""
    import asyncio
    from app.db.database import AsyncSessionLocal

    # Warm up DB connection pool
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(__import__("sqlalchemy").text("SELECT 1"))
    except Exception as exc:
        print(f"[warmup] DB ping failed: {exc}")

    # Warm up LLM (loads model into RAM, keeps it alive)
    if settings.llm_provider.lower() == "ollama":
        try:
            import httpx
            async with httpx.AsyncClient(timeout=120) as client:
                await client.post(
                    f"{settings.ollama_base_url}/api/generate",
                    json={"model": settings.ollama_model, "prompt": "", "keep_alive": -1},
                )
            print(f"[warmup] Ollama model '{settings.ollama_model}' loaded into RAM")
        except Exception as exc:
            print(f"[warmup] Ollama warmup failed: {exc}")
    else:
        print(f"[warmup] LLM provider '{settings.llm_provider}' — no warmup needed")


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="AI-powered fallout order analysis and resolution microservice.",
    lifespan=lifespan,
)

app.include_router(fallout_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": settings.app_title, "version": settings.app_version}


@app.get("/health/llm", tags=["Health"])
async def llm_health_check():
    """Quick connectivity check — sends a single word to the LLM and returns the reply."""
    from app.service.llm_service import get_ai_suggestion
    try:
        reply = await get_ai_suggestion("Reply with only the word: OK")
        return {
            "status": "ok",
            "provider": settings.llm_provider,
            "model": _active_model(),
            "reply": reply.strip(),
        }
    except Exception as exc:
        return {
            "status": "error",
            "provider": settings.llm_provider,
            "model": _active_model(),
            "error": f"{type(exc).__name__}: {exc}",
        }


def _active_model() -> str:
    p = settings.llm_provider.lower()
    if p == "groq":
        return settings.groq_model
    if p == "anthropic":
        return settings.anthropic_model
    if p == "gemini":
        return settings.gemini_model
    return settings.ollama_model
