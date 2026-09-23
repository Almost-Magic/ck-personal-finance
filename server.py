"""Standalone CK Personal Finance cockpit. PostgreSQL and pgvector required."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.auth import FinanceAuthMiddleware
from app.routes import personal_finance
from app.services.personal_finance_store import init_personal_finance_store


@asynccontextmanager
async def lifespan(app):
    init_personal_finance_store()
    yield


app = FastAPI(title="CK Personal Finance", version="1.0.0", lifespan=lifespan)
app.add_middleware(FinanceAuthMiddleware)
app.include_router(personal_finance.router, prefix="/api")
public_dir = Path(__file__).resolve().parent / "public"
app.mount("/static", StaticFiles(directory=str(public_dir)), name="static")


@app.get("/api/health")
async def health():
    return {"status": "ok", "product": "CK Personal Finance"}


@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    if full_path == "api" or full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"error": "Not found"})
    return FileResponse(public_dir / "index.html")


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)


@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    error_id = uuid4().hex
    logging.getLogger(__name__).exception("Unhandled request error id=%s path=%s", error_id, request.url.path)
    return JSONResponse(status_code=500, content={"error": "Internal server error.", "error_id": error_id})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=int(os.environ.get("PORT", "5124")))
