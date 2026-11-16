from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api.auth import router as auth_router
from .model import Base
from .utils.postgres import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Enterprise RAG API", version="1.0.0", lifespan=lifespan)
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
