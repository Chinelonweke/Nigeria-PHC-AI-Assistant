"""
Groq API Service
Handles interactions with Groq's language models
"""

from groq import Groq
from typing import Dict, Optional, List
import json

from backend.core.config import settings
from backend.core.logger import get_logger
from backend.services.cache_service import cache_service

logger = get_logger(__name__)

# CRITICAL: MUST BE THIS MODEL!
DEFAULT_MODEL = "llama-3.1-8b-instant"


class GroqService:
    """
    Service for interacting with Groq API
    Handles LLM calls for triage and analysis
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        """Initialize Groq service"""
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        
        if not self.client:
            logger.warning("⚠️ Groq API key not found - service will use fallback")
        else:
            logger.info(f"✅ Groq Service initialized (Model: {self.model})")
    
    def analyze_symptoms(
        self,
        symptoms: str,
        patient_info: Optional[Dict] = None,
        context: Optional[str] = None,
        language: str = "english"
    ) -> Dict:
        """
        Analyze symptoms using Groq LLM
        
        Args:
            symptoms: Patient symptoms description
            patient_info: Additional patient information (age, gender, etc.)
            context: Additional context for analysis
            language: Language for response
            
        Returns:
            Dict with diagnosis and recommendations
        """
        try:
            if not self.client:
                logger.warning("⚠️ Groq client not available, using fallback")
                return self._fallback_analysis(symptoms)
            
            logger.info(f"🩺 Analyzing symptoms in {language}")
            logger.info(f"🤖 Using model: {self.model}")
            
            # Check cache first
            cache_key = f"symptom_analysis_{symptoms}_{patient_info}_{language}"
            cached = cache_service.get(cache_key)
            if cached:
                logger.info("✅ Using cached analysis")
                return cached
            
            # Build prompt
            prompt = self._build_triage_prompt(symptoms, patient_info, context, language)
            
            # Call Groq API
            logger.info("🤖 Calling Groq API...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an experienced medical triage assistant helping healthcare workers in Nigeria. Provide preliminary assessments based on symptoms."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            logger.info("✅ Groq API call successful")
            
            # Parse response
            result = self._parse_triage_response(response.choices[0].message.content)
            
            # Cache result
            cache_service.set(cache_key, result, ttl=3600)
            
            logger.info(f"✅ Analysis complete: {result.get('likely_diagnosis', 'Unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error analyzing symptoms: {e}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            return self._fallback_analysis(symptoms)
    
    def _build_triage_prompt(
        self,
        symptoms: str,
        patient_info: Optional[Dict],
        context: Optional[str],
        language: str
    ) -> str:
        """Build prompt for symptom analysis"""
        prompt = f"""Analyze these symptoms and provide a preliminary triage assessment:

Symptoms: {symptoms}
"""
        
        if patient_info:
            if patient_info.get('age'):
                prompt += f"Age: {patient_info['age']} years\n"
            if patient_info.get('gender'):
                prompt += f"Gender: {patient_info['gender']}\n"
        
        if context:
            prompt += f"\nAdditional Context: {context}\n"
        
        prompt += f"""
Please provide your assessment in {language} with the following information:
1. Most likely diagnosis or condition
2. Urgency level (Routine, Urgent, or Critical)
3. Confidence level (Low, Medium, High)
4. Recommended action for healthcare worker
5. Tests that should be performed
6. Whether referral to specialist is needed

Format your response as JSON with these keys:
- likely_diagnosis
- urgency_level
- confidence
- recommended_action
- tests_needed (array)
- referral_needed (boolean)
- notes
"""
        
        return prompt
    
    def _parse_triage_response(self, response: str) -> Dict:
        """Parse LLM response into structured format"""
        try:
            # Try to extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = response[start:end]
                result = json.loads(json_str)
                logger.info("✅ Successfully parsed JSON response")
                return result
            else:
                # Fallback: parse text response
                logger.warning("⚠️ No JSON found, parsing as text")
                return {
                    'likely_diagnosis': 'Analysis completed',
                    'urgency_level': 'Routine',
                    'confidence': 'Medium',
                    'recommended_action': response,
                    'tests_needed': [],
                    'referral_needed': False,
                    'notes': response
                }
        except json.JSONDecodeError:
            logger.warning("⚠️ Could not parse JSON response, using text")
            return {
                'likely_diagnosis': 'See detailed notes',
                'urgency_level': 'Routine',
                'confidence': 'Medium',
                'recommended_action': response,
                'tests_needed': [],
                'referral_needed': False,
                'notes': response
            }
    
    def _fallback_analysis(self, symptoms: str) -> Dict:
        """Fallback analysis when API is unavailable"""
        logger.warning("⚠️ Using fallback analysis (Groq API unavailable)")
        
        # Simple keyword-based analysis
        symptoms_lower = symptoms.lower()
        
        # Critical symptoms
        if any(word in symptoms_lower for word in ['chest pain', 'difficulty breathing', 'severe bleeding', 'unconscious']):
            urgency = 'Critical'
            action = 'Immediate medical attention required. Transfer to emergency department.'
        # Urgent symptoms
        elif any(word in symptoms_lower for word in ['high fever', 'severe pain', 'vomiting', 'diarrhea']):
            urgency = 'Urgent'
            action = 'Patient should be seen within 1-2 hours. Monitor vital signs.'
        # Routine
        else:
            urgency = 'Routine'
            action = 'Schedule regular consultation. Provide symptomatic treatment.'
        
        return {
            'likely_diagnosis': 'Preliminary assessment - requires clinical evaluation',
            'urgency_level': urgency,
            'confidence': 'Low',
            'recommended_action': action,
            'tests_needed': ['Complete physical examination', 'Vital signs check'],
            'referral_needed': urgency == 'Critical',
            'notes': 'This is a fallback assessment. Groq API is not available - check API key or network connection.'
        }
    
    def translate_text(self, text: str, target_language: str) -> str:
        """Translate text to target language"""
        try:
            if not self.client:
                return text
            
            logger.info(f"🌍 Translating to {target_language}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a translator. Translate the following text to {target_language}."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            translated = response.choices[0].message.content
            logger.info("✅ Translation complete")
            return translated
            
        except Exception as e:
            logger.error(f"❌ Translation error: {e}")
            return text


# Global instance
groq_service = GroqService()


def get_groq_service() -> GroqService:
    """Get Groq service instance"""
    return groq_service