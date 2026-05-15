from fastapi import APIRouter
from backend.core.state import state

router = APIRouter()

def clamp(val, min_v, max_v):
    return max(min_v, min(max_v, val))

@router.get("/settings")
def get_settings():
    return {
        "deploy_pct": state.get("deploy_pct"),
        "max_exposure_pct": state.get("max_exposure_pct"),
        "risk_per_trade": state.get("risk_per_trade"),
    }

@router.post("/settings")
def update_settings(payload: dict):

    if "deploy_pct" in payload:
        state["deploy_pct"] = clamp(payload["deploy_pct"], 0.01, 1.0)

    if "max_exposure_pct" in payload:
        state["max_exposure_pct"] = clamp(payload["max_exposure_pct"], 0.01, 1.0)

    if "risk_per_trade" in payload:
        state["risk_per_trade"] = clamp(payload["risk_per_trade"], 0.001, 0.05)


    if "trading_enabled" in payload:
        state["trading_enabled"] = bool(payload["trading_enabled"])

    return {"status": "updated", "settings": get_settings()}