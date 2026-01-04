from fastapi import APIRouter

from backend.services.controller_runner import start_controller, stop_controller
from backend.utils.event_log import log_event

router = APIRouter()

@router.post("/controller/start")
def controller_start():
    start_controller()
    log_event("controller.api.start")
    return {"ok": True}

@router.post("/controller/stop")
def controller_stop():
    stop_controller()
    log_event("controller.api.stop")
    return {"ok": True}
