"""
Pydantic Schemas for API Request/Response Validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================
# TRIAGE SCHEMAS
# ============================================

class PatientInfo(BaseModel):
    """Patient information for triage"""
    age: Optional[int] = Field(None, ge=0, le=150, description="Patient age")
    gender: Optional[str] = Field(None, description="Patient gender (M/F)")
    medical_history: Optional[str] = Field(None, description="Relevant medical history")


class TriageRequest(BaseModel):
    """Request for symptom analysis"""
    symptoms: str = Field(..., min_length=3, description="Patient symptoms description")
    language: str = Field(default="english", description="Language: english, pidgin, hausa, yoruba, igbo")
    patient_info: Optional[PatientInfo] = Field(None, description="Optional patient information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symptoms": "Fever for 3 days, headache, body aches",
                "language": "english",
                "patient_info": {
                    "age": 30,
                    "gender": "M"
                }
            }
        }


class TriageResponse(BaseModel):
    """Response from symptom analysis"""
    likely_diagnosis: str
    urgency_level: str
    confidence: str
    recommended_action: str
    tests_needed: List[str]
    treatment_suggestions: List[str]
    red_flags: List[str]
    referral_needed: bool
    explanation: str
    timestamp: str


# ============================================
# INVENTORY/STOCKOUT SCHEMAS
# ============================================

class StockoutPredictionRequest(BaseModel):
    """Request for stockout prediction"""
    item_id: Optional[str] = Field(None, description="Specific item ID")
    facility_id: Optional[str] = Field(None, description="Specific facility ID")
    current_stock: Optional[int] = Field(None, ge=0, description="Current stock level")
    reorder_level: Optional[int] = Field(None, ge=0, description="Reorder threshold")
    last_restock_date: Optional[str] = Field(None, description="Last restock date (YYYY-MM-DD)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "item_id": "ITPHC_00001",
                "facility_id": "PHC_00003",
                "current_stock": 50,
                "reorder_level": 30,
                "last_restock_date": "2024-09-01"
            }
        }


class StockoutPredictionResponse(BaseModel):
    """Response from stockout prediction"""
    item_id: str
    facility_id: str
    current_stock: int
    reorder_level: int
    days_until_stockout: int
    stockout_date: str
    urgency: str
    should_reorder: bool
    confidence: float
    prediction_date: str


# ============================================
# CHAT SCHEMAS
# ============================================

class ChatMessageRequest(BaseModel):
    """Request to send a chat message"""
    session_id: str = Field(..., description="Unique session identifier")
    message: str = Field(..., min_length=1, description="User message")
    language: str = Field(default="english", description="Language for response")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_123",
                "message": "What are the symptoms of malaria?",
                "language": "english"
            }
        }


class ChatMessageResponse(BaseModel):
    """Response from chat message"""
    session_id: str
    user_message: str
    assistant_message: str
    language: str
    timestamp: str


class ChatHistoryResponse(BaseModel):
    """Response with chat history"""
    session_id: str
    messages: List[Dict[str, Any]]
    total_messages: int
    timestamp: str


# ============================================
# DASHBOARD SCHEMAS
# ============================================

class DashboardStatsResponse(BaseModel):
    """Response with dashboard statistics"""
    total_facilities: int
    operational_facilities: int
    total_patients: int
    total_inventory_items: int
    low_stock_items: int
    total_health_workers: int
    recent_patient_stats: Dict[str, Any]
    worker_stats: Dict[str, Any]
    last_updated: str


class FacilitySearchRequest(BaseModel):
    """Request to search facilities"""
    state: Optional[str] = Field(None, description="State name")
    lga: Optional[str] = Field(None, description="Local Government Area")
    operational_only: bool = Field(default=True, description="Only operational facilities")


class InventoryStatusRequest(BaseModel):
    """Request for inventory status"""
    facility_id: Optional[str] = Field(None, description="Specific facility")
    low_stock_only: bool = Field(default=False, description="Only low stock items")