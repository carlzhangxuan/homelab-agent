import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from routers import chat, homelab
import collector


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(collector.collect_loop())
    yield
    task.cancel()


app = FastAPI(title="homelab-tools", lifespan=lifespan)

app.include_router(chat.router, prefix="/v1")
app.include_router(homelab.router, prefix="/homelab")


@app.get("/health")
def health():
    return {"status": "ok"}
