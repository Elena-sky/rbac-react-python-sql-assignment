from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends

from app.api.authz import require_admin_or_manager
from app.models import MetricsStubPublic

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get(
    "/",
    dependencies=[Depends(require_admin_or_manager())],
    response_model=MetricsStubPublic,
)
def read_metrics_stub() -> Any:
    return {
        "status": "ok",
        "generated_at": datetime.now(timezone.utc),
        "summary": {
            "users_total": 0,
            "active_users": 0,
            "reports_generated_today": 0,
        },
    }
