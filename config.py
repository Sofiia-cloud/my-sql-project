# config.py
from dataclasses import dataclass
from typing import Dict, Any
import logging

@dataclass
class PgConfig:
    host: str = "localhost"
    port: int = 5432
    dbname: str = "ddos_mlops_db"
    user: str = "postgres"
    password: str = "root"
    sslmode: str = "prefer"

# Настройка логирования
def setup_logging():
    logging.basicConfig(
        filename='app.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        encoding='utf-8'
    )

# Стили и цвета
STYLES = {
    "primary_color": "#5b856a",
    "secondary_color": "#345e49",
    "accent_color": "#34db69",
    "success_color": "#27ae60",
    "danger_color": "#e74c3c",
    "warning_color": "#f39c12",
    "light_color": "#ecf0f1",
    "dark_color": "#182e20",
    "text_color": "#2c503a",
    "background_color": "#f8f9fa"
}