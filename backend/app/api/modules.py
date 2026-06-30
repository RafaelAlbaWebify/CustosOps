from fastapi import APIRouter

from app.services.modules import get_modules

router = APIRouter(prefix="/api")


@router.get("/modules")
def list_modules() -> dict:
    return {"modules": [module.model_dump() for module in get_modules()]}