"""
Services module initialization
Handles optional services gracefully
"""

from backend.core.logger import get_logger

logger = get_logger(__name__)

# Core services (always available)
from backend.services.s3_service import s3_service, S3Service
from backend.services.cache_service import cache_service, CacheService
from backend.services.groq_service import groq_service, GroqService
from backend.services.model_service import model_service, ModelService

# Optional services (may not be available)
# Whisper Service
try:
    from backend.services.whisper_service import whisper_service, WhisperService
    WHISPER_AVAILABLE = True
except Exception as e:
    logger.warning(f"⚠️ Whisper service not available: {e}")
    whisper_service = None
    WhisperService = None
    WHISPER_AVAILABLE = False

# TTS Service
try:
    from backend.services.tts_service import tts_service, TTSService
    TTS_AVAILABLE = True
except Exception as e:
    logger.warning(f"⚠️ TTS service not available: {e}")
    tts_service = None
    TTSService = None
    TTS_AVAILABLE = False

# Translation Service
try:
    from backend.services.translation_service import translation_service, TranslationService
    TRANSLATION_AVAILABLE = True
except Exception as e:
    logger.warning(f"⚠️ Translation service not available: {e}")
    translation_service = None
    TranslationService = None
    TRANSLATION_AVAILABLE = False

__all__ = [
    # Core services
    "s3_service",
    "cache_service",
    "groq_service",
    "model_service",
    "S3Service",
    "CacheService",
    "GroqService",
    "ModelService",
    # Optional services
    "whisper_service",
    "tts_service",
    "translation_service",
    "WhisperService",
    "TTSService",
    "TranslationService",
    # Availability flags
    "WHISPER_AVAILABLE",
    "TTS_AVAILABLE",
    "TRANSLATION_AVAILABLE",
]

# Log service availability
logger.info("=" * 60)
logger.info("SERVICE AVAILABILITY:")
logger.info(f"  ✅ S3 Service: Available")
logger.info(f"  ✅ Cache Service: Available")
logger.info(f"  ✅ Groq Service: Available")
logger.info(f"  ✅ Model Service: Available")
logger.info(f"  {'✅' if WHISPER_AVAILABLE else '⚠️'} Whisper Service: {'Available' if WHISPER_AVAILABLE else 'Disabled'}")
logger.info(f"  {'✅' if TTS_AVAILABLE else '⚠️'} TTS Service: {'Available' if TTS_AVAILABLE else 'Disabled'}")
logger.info(f"  {'✅' if TRANSLATION_AVAILABLE else '⚠️'} Translation Service: {'Available' if TRANSLATION_AVAILABLE else 'Disabled'}")
logger.info("=" * 60)