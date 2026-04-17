from fastapi import FastAPI
from routers import chat, homelab

app = FastAPI(title="homelab-tools")

app.include_router(chat.router, prefix="/v1")
app.include_router(homelab.router, prefix="/homelab")


@app.get("/health")
def health():
    return {"status": "ok"}
