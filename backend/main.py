from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.system import router as system_router
from backend.routes.logs import router as logs_router
from backend.routes.ai import router as ai_router
from backend.routes.controller import router as controller_router

from backend.services.controller_runner import start_controller


app = FastAPI(title="Power Trading System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system_router)
app.include_router(logs_router)
app.include_router(ai_router, prefix="/ai")
app.include_router(controller_router)


@app.on_event("startup")
def _startup():
    # Optional: disable autostart during dev by setting PTS_AUTOSTART=0
    import os
    if os.getenv("PTS_AUTOSTART", "1") == "1":
        start_controller(tick_sleep_s=0.2, checkpoint_every=20)


@app.get("/")
def root():
    return {"status": "Power Trading System ONLINE"}
