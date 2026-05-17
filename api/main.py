import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.parse import router as parse_router
from routers.extract import router as extract_router
from routers.generate import router as generate_router

load_dotenv()

app = FastAPI(
    title="事前確定届出書 自動生成 API",
    version="0.1.0",
)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

app.include_router(parse_router)
app.include_router(extract_router)
app.include_router(generate_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
