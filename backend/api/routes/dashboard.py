"""
Dashboard Endpoints
System statistics and monitoring data
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from backend.core.logger import get_logger
from backend.data.data_loader import data_loader
from backend.models.schemas import DashboardStatsResponse, FacilitySearchRequest

logger = get_logger(__name__)

router = APIRouter()


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats():
    """
    Get comprehensive dashboard statistics
    
    Returns:
    - Total facilities, patients, inventory
    - Low stock alerts
    - Recent patient statistics
    - Worker statistics
    """
    try:
        logger.info("📊 Getting dashboard statistics")
        
        # Get comprehensive summary
        summary = data_loader.get_dashboard_summary()
        
        response = DashboardStatsResponse(
            total_facilities=summary.get('total_facilities', 0),
            operational_facilities=summary.get('operational_facilities', 0),
            total_patients=summary.get('total_patients', 0),
            total_inventory_items=summary.get('total_inventory_items', 0),
            low_stock_items=summary.get('low_stock_items', 0),
            total_health_workers=summary.get('total_health_workers', 0),
            recent_patient_stats=summary.get('recent_patient_stats', {}),
            worker_stats=summary.get('worker_stats', {}),
            last_updated=summary.get('last_updated', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        
        logger.info("✅ Dashboard stats retrieved")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/facilities")
async def search_facilities(
    state: Optional[str] = Query(None, description="Filter by state"),
    lga: Optional[str] = Query(None, description="Filter by LGA"),
    operational_only: bool = Query(True, description="Only operational facilities")
):
    """
    Search and filter facilities
    
    Args:
        state: State name
        lga: Local Government Area
        operational_only: Show only functional facilities
    
    Returns:
        List of matching facilities
    """
    try:
        logger.info(f"🏥 Searching facilities (state: {state}, lga: {lga})")
        
        # Search facilities
        facilities_df = data_loader.search_facilities(
            state=state,
            lga=lga,
            operational_only=operational_only
        )
        
        if facilities_df.empty:
            return {
                "facilities": [],
                "total": 0,
                "filters": {
                    "state": state,
                    "lga": lga,
                    "operational_only": operational_only
                },
                "timestamp": datetime.now().isoformat()
            }
        
        # Convert to list
        facilities = facilities_df.to_dict('records')
        
        # Get state distribution
        state_dist = facilities_df['state'].value_counts().to_dict() if 'state' in facilities_df.columns else {}
        
        return {
            "facilities": facilities,
            "total": len(facilities),
            "states": state_dist,
            "filters": {
                "state": state,
                "lga": lga,
                "operational_only": operational_only
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error searching facilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/facility/{facility_id}")
async def get_facility_details(facility_id: str):
    """
    Get detailed information about a specific facility
    
    Args:
        facility_id: Facility identifier
    
    Returns:
        Complete facility information
    """
    try:
        logger.info(f"🏥 Getting facility details: {facility_id}")
        
        facility = data_loader.get_facility_info(facility_id)
        
        if not facility:
            raise HTTPException(status_code=404, detail=f"Facility '{facility_id}' not found")
        
        return {
            "facility": facility,
            "facility_id": facility_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting facility details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patients/stats")
async def get_patient_stats(
    facility_id: Optional[str] = Query(None, description="Filter by facility"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """
    Get patient statistics
    
    Args:
        facility_id: Optional facility filter
        days: Number of recent days to include (1-365)
    
    Returns:
        Patient visit statistics
    """
    try:
        logger.info(f"👥 Getting patient stats (facility: {facility_id}, days: {days})")
        
        stats = data_loader.get_patient_statistics(
            facility_id=facility_id,
            days=days
        )
        
        return {
            "statistics": stats,
            "facility_id": facility_id,
            "days_analyzed": days,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting patient stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/diseases/trends")
async def get_disease_trends(
    disease: str = Query(..., description="Disease name (e.g., Malaria)"),
    months: int = Query(6, ge=1, le=24, description="Number of months to analyze")
):
    """
    Get disease trend over time
    
    Args:
        disease: Disease name
        months: Number of months to analyze (1-24)
    
    Returns:
        Monthly disease trends with cases and deaths
    """
    try:
        logger.info(f"📈 Getting disease trends: {disease} ({months} months)")
        
        trends_df = data_loader.get_disease_trends(disease, months=months)
        
        if trends_df.empty:
            return {
                "trends": [],
                "disease": disease,
                "months_analyzed": months,
                "total_cases": 0,
                "total_deaths": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        # Convert to list
        trends = trends_df.to_dict('records')
        
        # Calculate totals
        total_cases = trends_df['total_cases'].sum() if 'total_cases' in trends_df.columns else 0
        total_deaths = trends_df['total_deaths'].sum() if 'total_deaths' in trends_df.columns else 0
        
        return {
            "trends": trends,
            "disease": disease,
            "months_analyzed": months,
            "total_cases": int(total_cases),
            "total_deaths": int(total_deaths),
            "death_rate": round((total_deaths / total_cases * 100), 2) if total_cases > 0 else 0,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting disease trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workers/stats")
async def get_worker_stats(facility_id: Optional[str] = Query(None, description="Filter by facility")):
    """
    Get health worker statistics
    
    Args:
        facility_id: Optional facility filter
    
    Returns:
        Worker distribution and statistics
    """
    try:
        logger.info(f"👨‍⚕️ Getting worker stats (facility: {facility_id})")
        
        stats = data_loader.get_worker_statistics(facility_id=facility_id)
        
        return {
            "statistics": stats,
            "facility_id": facility_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting worker stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))