"""
Test all services
"""

print("\n" + "=" * 60)
print("TESTING ALL SERVICES")
print("=" * 60)

# Test 1: Configuration
print("\n📋 1. Configuration")
try:
    from backend.core.config import settings
    print(f"✅ App: {settings.APP_NAME}")
    print(f"✅ Bucket: {settings.S3_BUCKET_NAME}")
except Exception as e:
    print(f"❌ Config error: {e}")

# Test 2: Logger
print("\n📋 2. Logger")
try:
    from backend.core.logger import get_logger
    logger = get_logger("test")
    logger.info("Logger working!")
    print("✅ Logger working")
except Exception as e:
    print(f"❌ Logger error: {e}")

# Test 3: S3 Service
print("\n📋 3. S3 Service")
try:
    from backend.services.s3_service import s3_service
    files = s3_service.list_files()
    print(f"✅ S3 connected - {len(files)} files found")
except Exception as e:
    print(f"❌ S3 error: {e}")

# Test 4: Cache Service
print("\n📋 4. Cache Service")
try:
    from backend.services.cache_service import cache_service
    cache_service.set("test", "value")
    value = cache_service.get("test")
    print(f"✅ Cache working - retrieved: {value}")
except Exception as e:
    print(f"❌ Cache error: {e}")

# Test 5: Groq Service
print("\n📋 5. Groq Service")
try:
    from backend.services.groq_service import groq_service
    print("✅ Groq service initialized")
except Exception as e:
    print(f"❌ Groq error: {e}")

# Test 6: Model Service
print("\n📋 6. Model Service")
try:
    from backend.services.model_service import model_service
    print("✅ Model service initialized")
except Exception as e:
    print(f"❌ Model error: {e}")

print("\n" + "=" * 60)
print("SERVICE TESTS COMPLETE")
print("=" * 60)