import logging, sys, os
from datetime import datetime

def get_logger(name: str):
    os.makedirs("storage/logs", exist_ok=True)
    log_file = f"storage/logs/{datetime.now():%Y%m%d}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger(name)
