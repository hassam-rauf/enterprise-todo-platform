import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db import lifespan
from routes.tasks import router as tasks_router
from routes.chat import router as chat_router
from routes.jobs import router as jobs_router

load_dotenv()

def create_app() -> FastAPI:
    app = FastAPI(
        title="Todo Platform API",
        version="1.0.0",
        description="Enterprise Todo Platform — Hassam Rauf",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(tasks_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")
    app.include_router(jobs_router)

    @app.get("/health")
    async def health_check() -> dict:
        return {"status": "ok", "message": "Todo Platform API is running"}

    @app.get("/")
    async def root() -> dict:
        return {"message": "Enterprise Todo Platform API", "docs": "/docs"}

    return app

app = create_app()
