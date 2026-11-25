import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401
from app.api import campaigns, content, health, posts, segments
from app.config import Settings, cors_origin_list
from app.db import Base, make_engine, make_session_factory
from app.metrics import MetricsMiddleware
from app.seed import seed

logger = logging.getLogger("leaflet")


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings.log_level)
    engine = make_engine(settings.database_url)
    session_factory = make_session_factory(engine)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        if settings.auto_create_schema:
            Base.metadata.create_all(engine)
        if settings.seed_demo:
            with session_factory() as session:
                seed(session)
                session.commit()
            logger.info("demo records loaded")
        yield
        engine.dispose()

    app = FastAPI(title="Leaflet", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.sessionmaker = session_factory
    app.state.llm_transport = None
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origin_list(settings),
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(campaigns.router, prefix="/api")
    app.include_router(content.router, prefix="/api")
    app.include_router(segments.router, prefix="/api")
    app.include_router(posts.router, prefix="/api")
    return app


app = create_app()
