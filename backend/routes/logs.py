from fastapi import APIRouter, Query
from backend.utils.event_log import get_events

router = APIRouter()

@router.get("/logs")
def logs(limit: int = Query(50, ge=1, le=500)):
    return {
        "events": get_events(limit=limit)
    }
