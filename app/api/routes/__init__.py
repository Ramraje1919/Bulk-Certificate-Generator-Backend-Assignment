from app.api.routes.jobs import router as jobs_router
from app.api.routes.certificates import router as certificates_router
from app.api.routes.verification import router as verification_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.health import router as health_router

__all__ = [
    "jobs_router",
    "certificates_router",
    "verification_router",
    "dashboard_router",
    "health_router",
]
