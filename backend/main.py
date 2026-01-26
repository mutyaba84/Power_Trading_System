from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.system import router as system_router
from backend.routes.logs import router as logs_router
from backend.routes.ai import router as ai_router
from backend.routes.controller import router as controller_router
from backend.routes.api_adapter import router as api_router
from backend.routes import trader

from backend.services.controller_runner import start_controller

app = FastAPI(title="Power Trading System")

# --------------------
# CORS
# --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------
# ROUTES
# --------------------
app.include_router(system_router, prefix="/api")
app.include_router(logs_router, prefix="/api")
app.include_router(ai_router, prefix="/api/ai")
app.include_router(controller_router, prefix="/api")
app.include_router(api_router, prefix="/api")

# ✅ FIX: trader routes MUST be under /api
app.include_router(trader.router, prefix="/api")

# --------------------
# STARTUP
# --------------------
@app.on_event("startup")
def _startup():
    import os
    if os.getenv("PTS_AUTOSTART", "1") == "1":
        start_controller(tick_sleep_s=0.2, checkpoint_every=20)

# --------------------
# ROOT
# --------------------
@app.get("/")
def root():
    return {"status": "Power Trading System ONLINE"}
