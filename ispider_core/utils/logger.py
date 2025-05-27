import logging
import colorlog
from concurrent_log_handler import ConcurrentRotatingFileHandler
import os
import sys

class LoggerFactory:

    @staticmethod
    def create_logger(log_folder, log_file="ispider.log", log_level="INFO", stdout_flag=False):
        """
        Creates and returns a logger instance.

        Args:
            base_path (str): Base directory where logs should be stored.
            log_file (str): Log file name.
            log_level (str): Logging level (DEBUG, INFO, ERROR).
            stdout_flag (bool): Whether to log to stdout.

        Returns:
            logging.Logger: Configured logger instance.
        """
        log_file="ispider.log" # overwrite this for installed module
        
        # Ensure log folder exists
        os.makedirs(log_folder, exist_ok=True)
        full_log_file = os.path.join(log_folder, log_file)

        # Use a logger name derived from log file name (without extension)
        logger_name = log_file.replace(".log", "")
        logger = logging.getLogger(logger_name)

        # Prevent duplicate handlers
        if logger.handlers:
            return logger

        # Set log level
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        # Define formatters
        color_formatter = colorlog.ColoredFormatter(
            "%(cyan)s%(asctime)s%(reset)s | "
            "%(yellow)s%(levelname)s%(reset)s | "
            "%(cyan)s%(filename)s:%(lineno)s%(reset)s | "
            "%(purple)s[%(funcName)s]%(reset)s "
            ">>> %(yellow)s%(message)s%(reset)s"
        )

        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(filename)s:%(lineno)s | [%(funcName)s] | %(process)d >>> %(message)s"
        )

        # Add file handler
        file_handler = ConcurrentRotatingFileHandler(full_log_file, backupCount=5, maxBytes=5_000_000)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Optionally add stdout handler
        if stdout_flag:
            stdout_handler = logging.StreamHandler(sys.stdout)
            stdout_handler.setFormatter(color_formatter)
            logger.addHandler(stdout_handler)

        return logger
