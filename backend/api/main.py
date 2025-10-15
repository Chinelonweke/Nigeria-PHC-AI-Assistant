"""
FastAPI Main Application
Nigerian PHC AI Assistant API
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from datetime import datetime
from backend.services import groq_service
from backend.api.routes import health, triage, inventory, chat, dashboard, audio
from backend.core.config import settings
from backend.core.logger import get_logger

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Healthcare Assistant for Nigerian Primary Healthcare Centers",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for logging and timing
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and response times"""
    start_time = time.time()
    
    # Log request
    logger.info(f"📨 {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Log response
    logger.info(f"✅ {request.method} {request.url.path} - {response.status_code} ({duration:.2f}s)")
    
    # Add custom headers
    response.headers["X-Process-Time"] = str(duration)
    
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions"""
    logger.error(f"❌ Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )
app.include_router(audio.router, prefix="/api/audio", tags=["Audio"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "health": "/health"
    }


# Import and include routers (we'll create these next)
from backend.api.routes import health, triage, inventory, chat, dashboard

app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(triage.router, prefix="/api/triage", tags=["Triage"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["Inventory"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])


# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("=" * 60)
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"🌍 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🗄️ Data Source: {'Redshift' if settings.USE_REDSHIFT else 'S3'}")
    logger.info("=" * 60)

    from backend.services.groq_service import groq_service
    logger.info(f"🤖 Groq Service Status: {'Active' if groq_service.client else 'Fallback Mode'}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("=" * 60)
    logger.info("🛑 Shutting down application")
    logger.info("=" * 60)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )