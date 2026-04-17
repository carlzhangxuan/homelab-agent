"""OpenAI-compatible /v1/chat/completions — routes to configured backend."""
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from config import settings

router = APIRouter()


def _backend_url() -> str:
    return settings.active_backend.rstrip("/")


@router.post("/chat/completions")
async def chat_completions(request: Request):
    body = await request.body()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.active_api_key}",
    }
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{_backend_url()}/v1/chat/completions",
            content=body,
            headers=headers,
        )
    return StreamingResponse(
        iter([resp.content]),
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type", "application/json"),
    )


@router.get("/models")
async def list_models():
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{_backend_url()}/v1/models",
            headers={"Authorization": f"Bearer {settings.active_api_key}"},
        )
    return resp.json()
