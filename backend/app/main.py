"""FastAPI application factory."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app import __version__
from app.api.routes import admin, geo, history, materiel, military, research, system
from app.core.config import get_settings
from app.core.errors import register_error_handlers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app() -> FastAPI:
    settings = get_settings()
    settings.validate_for_runtime()
    app = FastAPI(
        title="War Atlas API",
        version=__version__,
        description="API de exploração histórica e militar. Dados públicos = registros publicados; administração requer autenticação.",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=None,
    )
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=False,
                       allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type"])
    register_error_handlers(app)
    for r in (system.router, history.router, military.router, materiel.router, geo.router, research.router, admin.router):
        app.include_router(r, prefix=settings.api_prefix)
    return app


app = create_app()
