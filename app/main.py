import logging

from fastapi import FastAPI

from app.api.routes import router

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Multi-Agent Meeting Assistant",
    description="基于 DeepSeek + LangGraph 的多智能体会议纪要系统",
    version="1.0.0",
)

app.include_router(router)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}



# http://localhost:8000/docs
