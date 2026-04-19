from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agent import router as agent_router
from app.api.artifacts import router as artifacts_router
from app.api.conversations import router as conversations_router
from app.api.dashboard import router as dashboard_router
from app.api.knowledge import router as knowledge_router
from app.api.projects import router as projects_router
from app.api.search import router as search_router
from app.api.tasks import router as tasks_router
from app.config import get_settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db(settings.database_url)
    yield


app = FastAPI(title="Research Builder Agent API", version="0.1.0", lifespan=lifespan)

settings = get_settings()
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router)
app.include_router(projects_router)
app.include_router(conversations_router)
app.include_router(knowledge_router)
app.include_router(artifacts_router)
app.include_router(tasks_router)
app.include_router(agent_router)
app.include_router(search_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
