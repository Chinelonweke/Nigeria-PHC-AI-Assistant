"""
Triage Endpoints
AI-powered symptom analysis and patient triage
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime

from backend.core.logger import get_logger
from backend.services.groq_service import groq_service
from backend.services.deduplication_service import deduplication_service
from backend.services.cache_service import cache_service
from backend.data.symptom_database import search_disease_by_symptoms, get_disease_info
from backend.models.schemas import TriageRequest, TriageResponse
from backend.core.database import db_service

logger = get_logger(__name__)

router = APIRouter()


@router.post("/analyze", response_model=TriageResponse)
async def analyze_symptoms(request: TriageRequest):
    """
    Analyze patient symptoms using AI with deduplication and caching.
    
    Steps:
    - Prevent duplicate analyses using query hashing.
    - Use Groq LLM for intelligent reasoning.
    - Merge with local symptom database.
    - Cache results for 24 hours.
    - Log analysis to DynamoDB.
    """
    try:
        # Generate unique query ID and check for duplicates
        query_content = {
            "symptoms": request.symptoms,
            "age": request.patient_info.age if request.patient_info else None,
            "gender": request.patient_info.gender if request.patient_info else None,
            "language": request.language
        }

        query_id, is_new = deduplication_service.get_or_create_query_id(query_content)

        if not is_new:
            logger.info("🔄 Duplicate query detected, checking cache...")
            cached_result = cache_service.get(f"triage_result_{query_id}")
            if cached_result:
                logger.info("✅ Returning cached triage result")
                return cached_result

        logger.info(f"🩺 Analyzing symptoms in {request.language}")

        # Step 1: Search symptom database for possible matches
        symptom_list = [s.strip() for s in request.symptoms.split(",")]
        possible_diseases = search_disease_by_symptoms(symptom_list, request.language)
        logger.info(f"   Found {len(possible_diseases)} possible diseases")

        # Step 2: Use Groq LLM for intelligent analysis
        patient_info_dict = request.patient_info.dict() if request.patient_info else None

        analysis = groq_service.analyze_symptoms(
            symptoms=request.symptoms,
            patient_info=patient_info_dict,
            language=request.language
        )

        # Step 3: Enhance with database info if available
        if analysis.get("likely_diagnosis"):
            disease_info = get_disease_info(analysis["likely_diagnosis"], request.language)
            if disease_info:
                if not analysis.get("tests_needed"):
                    analysis["tests_needed"] = disease_info.get("tests", [])
                if not analysis.get("treatment_suggestions"):
                    analysis["treatment_suggestions"] = disease_info.get("treatments", [])

        # Step 4: Prepare response
        response = TriageResponse(
            likely_diagnosis=analysis.get("likely_diagnosis", "Unknown"),
            urgency_level=analysis.get("urgency_level", "Routine"),
            confidence=analysis.get("confidence", "Medium"),
            recommended_action=analysis.get("recommended_action", "Consult healthcare worker"),
            tests_needed=analysis.get("tests_needed", []),
            treatment_suggestions=analysis.get("treatment_suggestions", []),
            red_flags=analysis.get("red_flags", []),
            referral_needed=analysis.get("referral_needed", False),
            explanation=analysis.get("explanation", ""),
            timestamp=datetime.now().isoformat()
        )

        # Step 5: Cache result for 24 hours
        cache_service.set(f"triage_result_{query_id}", response, ttl=86400)

        # Step 6: Log to database
        try:
            db_service.save_log(
                log_type="triage_analysis",
                message=f"Analyzed symptoms: {request.symptoms[:50]}...",
                data={
                    "diagnosis": response.likely_diagnosis,
                    "urgency": response.urgency_level,
                    "language": request.language,
                    "query_id": query_id,
                    "is_new_query": is_new
                }
            )
        except Exception as log_error:
            logger.warning(f"⚠️ Failed to log triage: {log_error}")

        logger.info(f"✅ Analysis complete: {response.likely_diagnosis} ({response.urgency_level})")
        return response

    except Exception as e:
        logger.error(f"❌ Error analyzing symptoms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/diseases")
async def list_diseases(language: str = "english"):
    """
    Get list of supported diseases.
    """
    try:
        from backend.data.symptom_database import SUPPORTED_DISEASES, get_all_diseases
        
        # Use the new function
        diseases = get_all_diseases(language)
        
        return {
            "diseases": diseases,
            "language": language,
            "total": len(diseases)
        }

    except Exception as e:
        logger.error(f"❌ Error listing diseases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/disease/{disease_id}")
async def get_disease_details(disease_id: str, language: str = "english"):
    """
    Get detailed information about a specific disease.
    """
    try:
        disease_info = get_disease_info(disease_id, language)
        if not disease_info:
            raise HTTPException(status_code=404, detail=f"Disease '{disease_id}' not found")

        return {
            "disease_id": disease_id,
            "language": language,
            "data": disease_info,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting disease details: {e}")
        raise HTTPException(status_code=500, detail=str(e))