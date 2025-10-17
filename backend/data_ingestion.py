"""
Loads synthetic/historical market data for simulation.
"""
import pandas as pd
from pathlib import Path
from utils.logger import get_logger

logger = get_logger("data_ingestion")

def load_data(symbol="BTCUSD"):
    data_path = Path("storage/historical_data") / f"{symbol}.csv"
    if data_path.exists():
        logger.info(f"Loading {symbol} data from {data_path}")
        return pd.read_csv(data_path)
    logger.warning(f"No data found for {symbol}, returning empty DataFrame")
    return pd.DataFrame()

