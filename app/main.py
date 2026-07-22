from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import chat, health
from app.core.logging import configure_logging
from app.retrieval.indexer import build_index


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    count = await build_index()
    app.state.indexed_docs = count
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="StreamRAG Agent", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
    )
    app.include_router(health.router)
    app.include_router(chat.router)
    return app


app = create_app()
