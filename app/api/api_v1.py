from fastapi import APIRouter
from app.api.routes.jobs import router as jobs_router
from app.api.routes.certificates import router as certificates_router
from app.api.routes.verification import router as verification_router
from app.api.routes.dashboard import router as dashboard_router

api_router = APIRouter()
api_router.include_router(jobs_router)
api_router.include_router(certificates_router)
api_router.include_router(verification_router)
api_router.include_router(dashboard_router)
