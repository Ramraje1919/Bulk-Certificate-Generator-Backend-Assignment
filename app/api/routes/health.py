from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Service health check")
def health_check(db: Session = Depends(get_db)):
    # Verify DB connectivity
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Verify storage writable
    storage_status = "ready" if settings.STORAGE_DIR.exists() else "not found"

    overall_status = "healthy" if db_status == "connected" else "degraded"

    return {
        "status": overall_status,
        "database": db_status,
        "storage": storage_status,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }
