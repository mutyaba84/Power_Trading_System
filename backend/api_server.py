from backend.ai_core.system_bootstrap import start_ai_services

@app.on_event("startup")
def boot_ai():
    start_ai_services()
