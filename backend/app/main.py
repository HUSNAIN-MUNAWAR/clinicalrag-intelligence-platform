from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes_health, routes_sources, routes_documents, routes_ingestion, routes_rag, routes_evaluation, routes_safety
from app.core.config import settings
from app.db.session import init_db


def create_app() -> FastAPI:
    init_db()
    app = FastAPI(title='ClinicalRAG Intelligence Platform API', version='0.1.0')
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
    for r in [routes_health.router, routes_sources.router, routes_documents.router, routes_ingestion.router, routes_rag.router, routes_evaluation.router, routes_safety.router]:
        app.include_router(r)
    return app
app = create_app()
