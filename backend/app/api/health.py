from fastapi import APIRouter

from app.config import PRODUCT_FULL_NAME, PRODUCT_NAME, PRODUCT_VERSION

router = APIRouter(prefix="/api")


@router.get("/health")
def get_health() -> dict:
    return {
        "status": "ok",
        "product": PRODUCT_NAME,
        "product_full_name": PRODUCT_FULL_NAME,
        "version": PRODUCT_VERSION,
    }