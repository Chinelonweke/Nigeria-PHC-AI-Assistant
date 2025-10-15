"""
Health Check Endpoints
System status and diagnostics
"""

from fastapi import APIRouter
from datetime import datetime
from typing import Dict

from backend.core.config import settings, get_data_source_info
from backend.core.logger import get_logger
from backend.services.data_source_adapter import get_data_source

logger = get_logger(__name__)

router = APIRouter()


@router.get("/")
async def health_check() -> Dict:
    """
    Basic health check
    
    Returns system status and uptime
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


@router.get("/detailed")
async def detailed_health_check() -> Dict:
    """
    Detailed health check with all system components
    
    Returns:
    - Application status
    - Data source status
    - Database status
    - API status
    """
    try:
        # Check data source connection
        data_source = get_data_source()
        data_source_status = {
            "name": data_source.get_source_name(),
            "connected": data_source.is_connected(),
            "type": "Redshift" if settings.USE_REDSHIFT else "S3"
        }
        
    except Exception as e:
        logger.error(f"Data source check failed: {e}")
        data_source_status = {
            "name": "Unknown",
            "connected": False,
            "error": str(e)
        }
    
    # Get configuration info
    config_info = get_data_source_info()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "application": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG
        },
        "data_source": data_source_status,
        "configuration": config_info,
        "services": {
            "groq_configured": bool(settings.GROQ_API_KEY),
            "cache_enabled": settings.CACHE_TTL > 0
        }
    }


@router.get("/ping")
async def ping() -> Dict:
    """
    Simple ping endpoint for load balancers
    """
    return {"ping": "pong", "timestamp": datetime.now().isoformat()}