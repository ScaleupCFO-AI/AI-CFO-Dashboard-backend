from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.health import router as health_router
from app.api.upload import router as upload_router
from app.api.query import router as query_router

app = FastAPI(
    title="AI CFO Dashboard – Project Jelly",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # must be False when using "*"
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(health_router)
app.include_router(upload_router)
app.include_router(query_router)
