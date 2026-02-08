"""
Dual Logging System: MongoDB + File Output.

Features:
- Logs to MongoDB collections (system_logs, operation_logs)
- Logs to rotating files (daily rotation, 30-day retention)
- ERROR logs mandatory to file
- Async MongoDB logging
- Log levels: DEBUG, INFO, WARNING, ERROR
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional
from queue import Queue
from threading import Thread, Lock

from loguru import logger as loguru_logger

from models.log import LogEntry, LogLevel, SystemLog, OperationLog
from core.exceptions import LogError


class MongoDBLogHandler:
    """Async handler for MongoDB logging."""
    
    def __init__(self, mongodb_client=None):
        self.mongodb_client = mongodb_client
        self._queue: Queue = Queue()
        self._lock = Lock()
        self._worker_thread: Optional[Thread] = None
        self._running = False
        self._buffer: list = []
        self._buffer_size = 100
        self._flush_interval = 5  # seconds
    
    def start(self):
        """Start the async logging worker."""
        if self._running:
            return
        
        self._running = True
        self._worker_thread = Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
    
    def stop(self):
        """Stop the logging worker and flush remaining logs."""
        self._running = False
        if self._worker_thread:
            self._flush_buffer()
            self._worker_thread.join(timeout=10)
    
    def _worker_loop(self):
        """Worker thread loop for async MongoDB writes."""
        last_flush = datetime.now()
        
        while self._running:
            try:
                # Process queue
                while not self._queue.empty():
                    log_entry = self._queue.get_nowait()
                    self._buffer.append(log_entry)
                    
                    if len(self._buffer) >= self._buffer_size:
                        self._flush_buffer()
                
                # Periodic flush
                if (datetime.now() - last_flush).seconds >= self._flush_interval:
                    if self._buffer:
                        self._flush_buffer()
                    last_flush = datetime.now()
                
                import time
                time.sleep(0.1)
                
            except Exception as e:
                # Log to stderr if MongoDB logging fails
                print(f"MongoDB logging error: {e}", file=sys.stderr)
    
    def _flush_buffer(self):
        """Flush buffered logs to MongoDB."""
        if not self._buffer or not self.mongodb_client:
            return
        
        try:
            with self._lock:
                logs_to_write = self._buffer[:]
                self._buffer = []
            
            # Separate logs by type
            system_logs = [log for log in logs_to_write if isinstance(log, SystemLog)]
            operation_logs = [log for log in logs_to_write if isinstance(log, OperationLog)]
            
            # Write to appropriate collections
            if system_logs and self.mongodb_client:
                collection = self.mongodb_client.system_logs
                docs = [log.to_mongodb_doc() for log in system_logs]
                collection.insert_many(docs)
            
            if operation_logs and self.mongodb_client:
                collection = self.mongodb_client.operation_logs
                docs = [log.to_mongodb_doc() for log in operation_logs]
                collection.insert_many(docs)
                
        except Exception as e:
            print(f"Failed to flush logs to MongoDB: {e}", file=sys.stderr)
    
    def emit(self, log_entry: LogEntry):
        """Queue a log entry for MongoDB writing."""
        if self._running:
            self._queue.put(log_entry)


class DualLogger:
    """
    Dual logging system that logs to both MongoDB and file.
    
    Features:
    - MongoDB: Async writes to system_logs and operation_logs collections
    - File: Daily rotation, 30-day retention, ERROR logs mandatory
    """
    
    def __init__(self, name: str = "app"):
        self.name = name
        self._mongodb_handler: Optional[MongoDBLogHandler] = None
        self._log_dir: Optional[Path] = None
        self._initialized = False
        self._mongodb_client = None
        
        # Configure loguru logger
        self._logger = loguru_logger.bind(name=name)
        self._configure_loguru()
    
    def _configure_loguru(self):
        """Configure loguru logger."""
        # Remove default handler
        loguru_logger.remove()
        
        # Console handler for development
        loguru_logger.add(
            sys.stdout,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} | {message}",
            level="DEBUG",
            colorize=True
        )
    
    def initialize(self, 
                   mongodb_client=None,
                   log_dir: str = "./logs",
                   system_level: str = "INFO",
                   operation_level: str = "INFO"):
        """
        Initialize the dual logger.
        
        Args:
            mongodb_client: Motor/MongoDB client
            log_dir: Directory for log files
            system_level: Log level for system logs
            operation_level: Log level for operation logs
        """
        if self._initialized:
            return
        
        self._mongodb_client = mongodb_client
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup MongoDB handler
        if mongodb_client:
            self._mongodb_handler = MongoDBLogHandler(mongodb_client)
            self._mongodb_handler.start()
        
        # Setup file handlers with rotation
        self._setup_file_handlers(system_level, operation_level)
        
        self._initialized = True
        self.info("Dual logger initialized")
    
    def _setup_file_handlers(self, system_level: str, operation_level: str):
        """Setup file logging with rotation."""
        # System logs
        system_log_path = self._log_dir / "system" / "system_{time:YYYY-MM-DD}.log"
        system_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        loguru_logger.add(
            str(system_log_path),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} | {message}",
            level=system_level,
            rotation="00:00",  # Daily rotation
            retention="30 days",
            encoding="utf-8",
            filter=lambda record: record["extra"].get("log_type") == "system"
        )
        
        # Operation logs
        operation_log_path = self._log_dir / "operation" / "operation_{time:YYYY-MM-DD}.log"
        operation_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        loguru_logger.add(
            str(operation_log_path),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} | {message}",
            level=operation_level,
            rotation="00:00",
            retention="30 days",
            encoding="utf-8",
            filter=lambda record: record["extra"].get("log_type") == "operation"
        )
        
        # ERROR logs (mandatory, includes all log types)
        error_log_path = self._log_dir / "error" / "error_{time:YYYY-MM-DD}.log"
        error_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        loguru_logger.add(
            str(error_log_path),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} | {message}",
            level="ERROR",
            rotation="00:00",
            retention="30 days",
            encoding="utf-8"
        )
    
    def _log(self, level: LogLevel, message: str, 
             log_type: str = "system",
             source: str = "system",
             metadata: Optional[Dict[str, Any]] = None,
             **kwargs):
        """Internal logging method."""
        # Create log entry for MongoDB
        if log_type == "system":
            log_entry = SystemLog(
                level=level,
                message=message,
                source=source,
                metadata=metadata or {},
                **kwargs
            )
        else:
            log_entry = OperationLog(
                level=level,
                message=message,
                source=source,
                metadata=metadata or {},
                **kwargs
            )
        
        # Log to MongoDB (async)
        if self._mongodb_handler:
            self._mongodb_handler.emit(log_entry)
        
        # Log to file via loguru
        extra = {"log_type": log_type, "name": self.name}
        extra.update(kwargs)
        
        log_method = getattr(self._logger, level.value.lower())
        log_method(message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log DEBUG level message."""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log INFO level message."""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log WARNING level message."""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log ERROR level message."""
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def shutdown(self):
        """Shutdown logger and cleanup."""
        if self._mongodb_handler:
            self._mongodb_handler.stop()
        self.info("Dual logger shutdown")


# Global logger instance
_logger_instance: Optional[DualLogger] = None
_logger_lock = Lock()


def get_logger(name: str = "app") -> DualLogger:
    """
    Get or create logger instance.
    
    Args:
        name: Logger name
    
    Returns:
        DualLogger instance
    """
    global _logger_instance
    
    with _logger_lock:
        if _logger_instance is None:
            _logger_instance = DualLogger(name)
        return _logger_instance


def initialize_logger(mongodb_client=None, log_dir: str = "./logs",
                     system_level: str = "INFO", operation_level: str = "INFO"):
    """
    Initialize the global logger.
    
    Args:
        mongodb_client: MongoDB client for async logging
        log_dir: Directory for log files
        system_level: System log level
        operation_level: Operation log level
    """
    logger = get_logger()
    logger.initialize(
        mongodb_client=mongodb_client,
        log_dir=log_dir,
        system_level=system_level,
        operation_level=operation_level
    )
    return logger


def shutdown_logger():
    """Shutdown the global logger."""
    global _logger_instance
    if _logger_instance:
        _logger_instance.shutdown()
        _logger_instance = None
