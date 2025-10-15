"""
Configuration Management
Loads and validates environment variables
Enhanced with Redshift support and fallback mechanisms
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # ============================================
    # AWS S3
    # ============================================
    AWS_ACCESS_KEY_ID: str = Field(default="", env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = Field(default="", env="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = "eu-north-1"
    S3_BUCKET_NAME: str = "datathon.phc"
    USE_S3: bool = Field(default=True, env="USE_S3")  # Added for clarity
    
    # ============================================
    # GROQ
    # ============================================
    GROQ_API_KEY: str = Field(default="", env="GROQ_API_KEY")
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    
    # ============================================
    # DATA SOURCE CONFIGURATION
    # ============================================
    USE_REDSHIFT: bool = Field(default=False, env="USE_REDSHIFT")
    DATA_SOURCE_PRIORITY: str = Field(default="redshift,s3", env="DATA_SOURCE_PRIORITY")
    
    # ============================================
    # AWS REDSHIFT
    # ============================================
    REDSHIFT_HOST: str = Field(default="", env="REDSHIFT_HOST")
    REDSHIFT_PORT: int = Field(default=5439, env="REDSHIFT_PORT")
    REDSHIFT_DATABASE: str = Field(default="", env="REDSHIFT_DATABASE")
    REDSHIFT_USER: str = Field(default="", env="REDSHIFT_USER")
    REDSHIFT_PASSWORD: str = Field(default="", env="REDSHIFT_PASSWORD")
    REDSHIFT_SCHEMA: str = Field(default="public", env="REDSHIFT_SCHEMA")
    REDSHIFT_MIN_CONNECTIONS: int = Field(default=1, env="REDSHIFT_MIN_CONNECTIONS")
    REDSHIFT_MAX_CONNECTIONS: int = Field(default=10, env="REDSHIFT_MAX_CONNECTIONS")
    
    # ============================================
    # DATABASE (DynamoDB)
    # ============================================
    DYNAMODB_TABLE_PREFIX: str = "phc_assistant"
    DYNAMODB_CHAT_TABLE: str = "phc_assistant_chat_history"
    DYNAMODB_LOGS_TABLE: str = "phc_assistant_logs"
    DYNAMODB_EMBEDDINGS_TABLE: str = "phc_assistant_embeddings"
    
    # ============================================
    # APPLICATION
    # ============================================
    ENVIRONMENT: str = "development"
    APP_NAME: str = "PHC AI Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    
    # ============================================
    # API
    # ============================================
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # ============================================
    # ML MODEL
    # ============================================
    STOCKOUT_MODEL_PATH: str = "./ml_models/stockout_model.pkl"
    
    # ============================================
    # VOICE & TRANSLATION
    # ============================================
    WHISPER_MODEL: str = "base"
    TTS_LANGUAGE: str = "en"
    ENABLE_TRANSLATION: bool = True
    
    # ============================================
    # CACHE
    # ============================================
    CACHE_TTL: int = 3600
    MAX_CACHE_SIZE: int = 1000
    
    # ============================================
    # VALIDATORS
    # ============================================
    
    @field_validator("CORS_ORIGINS", mode='before')
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.strip("[]").replace('"', '').split(",")]
        return v
    
    # ============================================
    # COMPUTED PROPERTIES
    # ============================================
    
    @property
    def redshift_url(self) -> Optional[str]:
        """
        Generate Redshift connection URL for SQLAlchemy
        
        Returns:
            Connection URL or None if not configured
        """
        if not self.is_redshift_configured():
            return None
        
        return (
            f"postgresql://{self.REDSHIFT_USER}:{self.REDSHIFT_PASSWORD}"
            f"@{self.REDSHIFT_HOST}:{self.REDSHIFT_PORT}"
            f"/{self.REDSHIFT_DATABASE}"
        )
    
    @property
    def data_source_list(self) -> List[str]:
        """
        Get prioritized list of data sources
        
        Returns:
            List of data sources in priority order
        """
        return [s.strip().lower() for s in self.DATA_SOURCE_PRIORITY.split(',')]
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    def is_redshift_configured(self) -> bool:
        """
        Check if Redshift is fully configured
        
        Returns:
            True if all Redshift credentials are present
        """
        return (
            self.USE_REDSHIFT and 
            bool(self.REDSHIFT_HOST) and
            bool(self.REDSHIFT_DATABASE) and
            bool(self.REDSHIFT_USER) and
            bool(self.REDSHIFT_PASSWORD)
        )
    
    def is_s3_configured(self) -> bool:
        """
        Check if S3 is fully configured
        
        Returns:
            True if AWS credentials are present
        """
        return (
            self.USE_S3 and
            bool(self.AWS_ACCESS_KEY_ID) and
            bool(self.AWS_SECRET_ACCESS_KEY)
        )
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_aws_config() -> dict:
    """Get AWS configuration dict"""
    return {
        "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
        "region_name": settings.AWS_REGION,
    }


def is_production() -> bool:
    """Check if running in production"""
    return settings.ENVIRONMENT == "production"


def get_data_source_info() -> dict:
    """
    Get comprehensive information about configured data sources
    
    Returns:
        Dict with data source configuration and status
    """
    return {
        "use_redshift": settings.USE_REDSHIFT,
        "redshift_configured": settings.is_redshift_configured(),
        "redshift_url": settings.redshift_url if settings.is_redshift_configured() else None,
        "s3_configured": settings.is_s3_configured(),
        "s3_bucket": settings.S3_BUCKET_NAME if settings.is_s3_configured() else None,
        "data_source_priority": settings.data_source_list,
        "primary_source": settings.data_source_list[0] if settings.data_source_list else None,
        "fallback_source": settings.data_source_list[1] if len(settings.data_source_list) > 1 else None,
    }


def get_redshift_connection_string() -> Optional[str]:
    """
    Get Redshift connection string (masked password)
    For logging purposes
    
    Returns:
        Masked connection string or None
    """
    if not settings.is_redshift_configured():
        return None
    
    return (
        f"postgresql://{settings.REDSHIFT_USER}:****"
        f"@{settings.REDSHIFT_HOST}:{settings.REDSHIFT_PORT}"
        f"/{settings.REDSHIFT_DATABASE}"
    )


# ============================================
# CONFIGURATION VALIDATION
# ============================================

def validate_configuration() -> dict:
    """
    Validate all configuration settings
    
    Returns:
        Dict with validation results
    """
    issues = []
    warnings = []
    
    # Check Groq API
    if not settings.GROQ_API_KEY:
        issues.append("GROQ_API_KEY not set - AI triage will not work")
    
    # Check data sources
    if not settings.is_redshift_configured() and not settings.is_s3_configured():
        issues.append("No data source configured - need either Redshift or S3")
    
    if settings.USE_REDSHIFT and not settings.is_redshift_configured():
        warnings.append("USE_REDSHIFT=True but Redshift not fully configured")
    
    # Check AWS credentials
    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        warnings.append("AWS credentials not set - S3 and other AWS services unavailable")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "data_sources": get_data_source_info()
    }


# ============================================
# MAIN (FOR TESTING)
# ============================================

if __name__ == "__main__":
    print("=" * 70)
    print("PHC AI ASSISTANT - CONFIGURATION TEST")
    print("=" * 70)
    
    print(f"\n📋 APPLICATION INFO")
    print(f"   Name: {settings.APP_NAME}")
    print(f"   Version: {settings.APP_VERSION}")
    print(f"   Environment: {settings.ENVIRONMENT}")
    print(f"   Debug: {settings.DEBUG}")
    
    print(f"\n🗄️ DATA SOURCES")
    ds_info = get_data_source_info()
    print(f"   Priority: {' → '.join(ds_info['data_source_priority'])}")
    print(f"   Primary: {ds_info['primary_source']}")
    print(f"   Fallback: {ds_info['fallback_source']}")
    
    print(f"\n📊 REDSHIFT")
    print(f"   Enabled: {settings.USE_REDSHIFT}")
    print(f"   Configured: {settings.is_redshift_configured()}")
    if settings.is_redshift_configured():
        print(f"   Host: {settings.REDSHIFT_HOST}")
        print(f"   Database: {settings.REDSHIFT_DATABASE}")
        print(f"   User: {settings.REDSHIFT_USER}")
        print(f"   Schema: {settings.REDSHIFT_SCHEMA}")
        print(f"   Connection: {get_redshift_connection_string()}")
    else:
        print(f"   Status: Not configured")
    
    print(f"\n📦 S3")
    print(f"   Enabled: {settings.USE_S3}")
    print(f"   Configured: {settings.is_s3_configured()}")
    if settings.is_s3_configured():
        print(f"   Bucket: {settings.S3_BUCKET_NAME}")
        print(f"   Region: {settings.AWS_REGION}")
    else:
        print(f"   Status: Not configured")
    
    print(f"\n🤖 AI SERVICES")
    print(f"   Groq API: {'✅ Configured' if settings.GROQ_API_KEY else '❌ Not configured'}")
    print(f"   Groq Model: {settings.GROQ_MODEL}")
    print(f"   Whisper Model: {settings.WHISPER_MODEL}")
    print(f"   Translation: {'✅ Enabled' if settings.ENABLE_TRANSLATION else '❌ Disabled'}")
    
    print(f"\n🌐 API")
    print(f"   Host: {settings.API_HOST}")
    print(f"   Port: {settings.API_PORT}")
    print(f"   Auto-reload: {settings.API_RELOAD}")
    
    print(f"\n✅ VALIDATION")
    validation = validate_configuration()
    
    if validation['valid']:
        print(f"   Status: ✅ All checks passed")
    else:
        print(f"   Status: ❌ Issues found")
    
    if validation['issues']:
        print(f"\n   ❌ ISSUES:")
        for issue in validation['issues']:
            print(f"      - {issue}")
    
    if validation['warnings']:
        print(f"\n   ⚠️ WARNINGS:")
        for warning in validation['warnings']:
            print(f"      - {warning}")
    
    print("\n" + "=" * 70)
    
    # Exit with error code if invalid
    import sys
    if not validation['valid']:
        sys.exit(1)