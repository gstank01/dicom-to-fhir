import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logging(log_file_prefix="app.log", level=logging.DEBUG):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    full_filename = f"{log_file_prefix}_{timestamp}.log"
    full_path = os.path.join(log_dir, full_filename)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    file_handler = RotatingFileHandler(full_path, maxBytes=1_000_000, backupCount=3)
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)

    logging.debug("Logging setup complete.")
