from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.modules import router as modules_router
from app.api.sample_findings import router as sample_findings_router
from app.config import PRODUCT_FULL_NAME, PRODUCT_VERSION

app = FastAPI(title=PRODUCT_FULL_NAME, version=PRODUCT_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(modules_router)
app.include_router(sample_findings_router)