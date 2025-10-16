"""
FastAPI application entry point
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any
import time

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.schemas.common import ErrorResponse, ErrorDetail

# Initialize logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager"""
    # Startup
    logger.info(
        "Starting ChaiWord Duck API",
        extra={"extra_data": {"version": settings.app_version, "env": settings.app_env}},
    )

    # Log CORS configuration
    logger.info(
        "CORS configuration",
        extra={
            "extra_data": {
                "allowed_origins": settings.cors_origins_list,
                "allow_credentials": settings.cors_allow_credentials,
            }
        },
    )

    yield

    # Shutdown
    logger.info("Shutting down ChaiWord Duck API")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="ChaiWord Duck Backend API - English Long Word Learning Platform",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件

    记录所有HTTP请求的详细信息，包括：
    - 请求方法、路径、headers
    - 响应状态码
    - 处理时间
    """

    async def dispatch(self, request: Request, call_next):
        """处理请求并记录日志"""
        start_time = time.time()

        # 提取请求信息
        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"
        origin_header = request.headers.get("origin", "no-origin")
        user_agent = request.headers.get("user-agent", "unknown")

        # 处理请求
        try:
            response = await call_next(request)
            status_code = response.status_code
            process_time = time.time() - start_time

            # 构建日志数据
            log_data = {
                "method": method,
                "path": path,
                "status_code": status_code,
                "client_host": client_host,
                "origin": origin_header,
                "user_agent": user_agent,
                "process_time_ms": round(process_time * 1000, 2),
            }

            # 根据状态码确定日志级别并记录
            if status_code < 400:
                logger.info(
                    f"{method} {path} - {status_code}",
                    extra={"extra_data": log_data},
                )
            elif status_code < 500:
                logger.warning(
                    f"{method} {path} - {status_code}",
                    extra={"extra_data": log_data},
                )
            else:
                logger.error(
                    f"{method} {path} - {status_code}",
                    extra={"extra_data": log_data},
                )

            return response

        except Exception as exc:
            process_time = time.time() - start_time
            logger.error(
                f"{method} {path} - Request processing failed",
                extra={
                    "extra_data": {
                        "method": method,
                        "path": path,
                        "client_host": client_host,
                        "origin": origin_header,
                        "process_time_ms": round(process_time * 1000, 2),
                        "error": str(exc),
                    }
                },
                exc_info=True,
            )
            raise


# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)


# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    全局HTTP异常处理器

    将FastAPI的HTTPException转换为统一的错误响应格式
    """
    # 如果detail是dict，说明是我们自定义的错误格式
    if isinstance(exc.detail, dict):
        error_code = exc.detail.get("code", "UNKNOWN_ERROR")
        error_message = exc.detail.get("message", "发生错误")
    else:
        # 否则是FastAPI默认的字符串detail
        error_code = "HTTP_ERROR"
        error_message = str(exc.detail)

    # 记录日志
    logger.warning(
        f"HTTP {exc.status_code} error: {error_message}",
        extra={
            "extra_data": {
                "path": str(request.url),
                "status_code": exc.status_code,
                "error_code": error_code,
            }
        },
    )

    # 返回统一格式错误响应
    error_response = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code=error_code,
            message=error_message,
        ),
    )

    # 准备响应headers（如果异常包含headers，则传递）
    response_headers = exc.headers if exc.headers is not None else {}

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode="json"),
        headers=response_headers,  # 保留原始异常的headers（如WWW-Authenticate）
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    全局Pydantic验证错误处理器

    将FastAPI默认的422错误转换为统一的错误响应格式
    """
    # 提取第一个错误信息
    errors = exc.errors()
    first_error = errors[0] if errors else {}

    # 构造错误消息
    field = " -> ".join(str(loc) for loc in first_error.get("loc", []))
    msg = first_error.get("msg", "验证失败")
    error_type = first_error.get("type", "validation_error")

    # 记录日志
    logger.warning(
        f"Request validation error: {field} - {msg}",
        extra={
            "extra_data": {
                "path": str(request.url),
                "error_type": error_type,
            }
        },
    )

    # 返回统一格式错误响应
    error_response = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message=f"{field}: {msg}" if field != "body" else msg,
        ),
    )

    return JSONResponse(
        status_code=422,
        content=error_response.model_dump(mode="json"),
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    404错误处理器

    记录所有未匹配的路由请求，帮助诊断路由问题
    """
    logger.warning(
        f"404 Not Found: {request.method} {request.url.path}",
        extra={
            "extra_data": {
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_host": request.client.host if request.client else "unknown",
                "origin": request.headers.get("origin", "no-origin"),
                "user_agent": request.headers.get("user-agent", "unknown"),
            }
        },
    )

    # 返回统一格式错误响应
    error_response = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code="NOT_FOUND",
            message="请求的资源不存在",
        ),
    )

    return JSONResponse(
        status_code=404,
        content=error_response.model_dump(mode="json"),
    )


# Health check endpoint
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.app_env,
    }


# Register API routers
from app.api.v1 import api_router as api_v1_router

app.include_router(api_v1_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
