import logging
import os
from pathlib import Path


LOG_PATH =  Path(__file__).parent / "logs" / "medmemory.log"


def get_logger(name : str) -> logging.Logger:
    """Get a configured logger that writes to both file and console."""

    logger = logging.getLogger(name)

    #Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)


    #File handler - detailed logs with timestamps
    file_handler = logging.FileHandler(LOG_PATH)
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(file_format)

    #Console handler - INFO and above only 
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter("%(levelname)s | %(name)s | %(message)s")
    console_handler.setFormatter(console_format)


    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger



    

    