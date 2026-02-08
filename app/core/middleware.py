"""
FastAPI middleware for CORS, logging, and error handling.
"""

import time
import uuid
from typing import Callable, Optional

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from core.logger import get_logger
from models.base import ErrorResponse

logger = get_logger("middleware")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate trace ID
        trace_id = str(uuid.uuid4())[:8]
        request.state.trace_id = trace_id
        
        # Log request
        start_time = time.time()
        logger.info(
            f"Request {request.method} {request.url.path}",
            log_type="operation",
            operation="http_request",
            trace_id=trace_id,
            request_data={
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
                "client": request.client.host if request.client else None,
            }
        )
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log response
            logger.info(
                f"Response {response.status_code} in {duration_ms}ms",
                log_type="operation",
                operation="http_response",
                trace_id=trace_id,
                duration_ms=duration_ms,
                response_data={
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                }
            )
            
            # Add trace ID to response headers
            response.headers["X-Trace-ID"] = trace_id
            
            return response
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            logger.error(
                f"Request failed: {str(e)}",
                log_type="operation",
                operation="http_error",
                trace_id=trace_id,
                duration_ms=duration_ms,
            )
            
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware to handle exceptions and return consistent error responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
            
        except Exception as e:
            trace_id = getattr(request.state, 'trace_id', 'unknown')
            
            logger.error(
                f"Unhandled exception: {str(e)}",
                log_type="system",
                source="error_middleware",
                trace_id=trace_id,
                metadata={"exception": str(e), "type": type(e).__name__}
            )
            
            # Return JSON error response
            from fastapi.responses import JSONResponse
            
            error_response = ErrorResponse(
                success=False,
                message="Internal server error",
                error_code="INTERNAL_ERROR",
                error_details={"trace_id": trace_id}
            )
            
            return JSONResponse(
                status_code=500,
                content=error_response.model_dump()
            )


def setup_middleware(app: FastAPI):
    """Setup all middleware for the FastAPI app."""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure based on your needs
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Request logging middleware
    app.add_middleware(RequestLoggingMiddleware)
    
    # Error handling middleware
    app.add_middleware(ErrorHandlingMiddleware)
    
    logger.info("Middleware setup complete")
