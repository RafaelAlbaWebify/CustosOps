from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dns import router as dns_router
from app.api.endpoint import router as endpoint_router
from app.api.health import router as health_router
from app.api.modules import router as modules_router
from app.api.reports import router as reports_router
from app.api.redaction_settings import router as redaction_settings_router
from app.api.windows_events import router as windows_events_router
from app.api.evidence_runs import router as evidence_runs_router
from app.api.app_log import router as app_log_router
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
app.include_router(endpoint_router)
app.include_router(dns_router)
app.include_router(reports_router)
app.include_router(redaction_settings_router)
app.include_router(windows_events_router)
app.include_router(evidence_runs_router)
app.include_router(app_log_router)
