from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.routes.ws import ws_router
from app.api.routes.reports import reports_router
from app.api.routes.health import health_router
from app.core.logger import setup_logging
from contextlib import asynccontextmanager
from app.routers.detection import router as detection_router
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield

app = FastAPI(title="Factify API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", include_in_schema=False)
async def serve_frontend():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Factify API is running"}

app.include_router(ws_router)
app.include_router(reports_router, tags=["Reports"])
app.include_router(health_router, tags=["Health"])
app.include_router(detection_router, tags=["Detection"])
