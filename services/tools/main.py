import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from prometheus_client import CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from routers import chat, homelab
from routers.prom import build_metrics
import collector


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(collector.collect_loop())
    yield
    task.cancel()


app = FastAPI(title="homelab-tools", lifespan=lifespan)

app.include_router(chat.router, prefix="/v1")
app.include_router(homelab.router, prefix="/homelab")


@app.get("/metrics", response_class=PlainTextResponse)
def prometheus_metrics():
    return PlainTextResponse(build_metrics(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
def health():
    return {"status": "ok"}
