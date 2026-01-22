from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.health import router as health_router
from app.api.company_baseline import router as company_baseline_router
from app.api.company_overview import router as company_overview_router
from app.api.upload import router as upload_router
from app.api.query import router as query_router

app = FastAPI(
    title="AI CFO Dashboard – Project Jelly",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",  # frontend dev server
        "http://127.0.0.1:8080",
        "http://localhost:8080/"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


app.include_router(health_router)
app.include_router(upload_router)
app.include_router(query_router)
app.include_router(company_baseline_router)
app.include_router(company_overview_router)
