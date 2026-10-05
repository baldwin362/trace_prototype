"""The FastAPI application. Run it with: uvicorn backend.api.main:app"""

from fastapi import FastAPI

from backend.api.health_route import health_router
from backend.api.scan_route import scan_router

app = FastAPI(title="Trace", description="Detects the technologies a company uses from its domain, with evidence.")
app.include_router(scan_router)
app.include_router(health_router)
