"""
Inventory Routes
API endpoints for inventory management and stockout prediction
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime

from backend.core.logger import get_logger
from backend.data.inventory_loader import inventory_loader
from backend.ml_models.stockout_predictor import stockout_predictor
from backend.services.cache_service import cache_service

logger = get_logger(__name__)

router = APIRouter()


@router.get("/status")
async def get_inventory_status(facility_id: Optional[str] = None):
    """
    Get overall inventory status
    
    Returns summary statistics
    """
    try:
        # Check cache first
        cache_key = f"inventory_status_{facility_id or 'all'}"
        cached = cache_service.get(cache_key)
        if cached:
            return cached
        
        # Load inventory
        inventory = inventory_loader.load_inventory(facility_id)
        
        if inventory.empty:
            return {
                'total_items': 0,
                'low_stock_count': 0,
                'critical_count': 0,
                'message': 'No inventory data available'
            }
        
        # Calculate statistics
        low_stock = inventory[inventory['stock_level'] <= inventory['reorder_level'] * 1.2]
        critical = inventory[inventory['stock_level'] <= inventory['reorder_level']]
        
        total_value = (inventory['stock_level'] * inventory.get('unit_price', 0)).sum()
        
        result = {
            'total_items': len(inventory),
            'low_stock_count': len(low_stock),
            'critical_count': len(critical),
            'total_value': float(total_value) if total_value else 0,
            'facilities_covered': inventory['facility_id'].nunique(),
            'last_updated': datetime.now().isoformat()
        }
        
        # Cache for 5 minutes
        cache_service.set(cache_key, result, ttl=300)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error getting inventory status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predict-stockouts")
async def predict_stockouts(
    facility_id: Optional[str] = None,
    alert_level: Optional[str] = Query(None, description="Filter by alert level: CRITICAL, WARNING, ATTENTION")
):
    """
    Predict stockouts for inventory items
    
    Returns list of predictions with alerts
    """
    try:
        logger.info(f"🔮 Predicting stockouts for facility: {facility_id or 'all'}")
        
        # Load inventory
        inventory = inventory_loader.load_inventory(facility_id)
        
        if inventory.empty:
            return {
                'predictions': [],
                'summary': {
                    'total_items': 0,
                    'critical_alerts': 0,
                    'warning_alerts': 0
                }
            }
        
        # Run predictions
        predictions = stockout_predictor.batch_predict(inventory)
        
        # Filter by alert level if specified
        if alert_level:
            predictions = [
                p for p in predictions 
                if p.get('alert_level') == alert_level.upper()
            ]
        
        # Create summary
        summary = {
            'total_items': len(predictions),
            'critical_alerts': len([p for p in predictions if p.get('alert_level') == 'CRITICAL']),
            'warning_alerts': len([p for p in predictions if p.get('alert_level') == 'WARNING']),
            'attention_alerts': len([p for p in predictions if p.get('alert_level') == 'ATTENTION']),
            'generated_at': datetime.now().isoformat()
        }
        
        return {
            'predictions': predictions,
            'summary': summary
        }
        
    except Exception as e:
        logger.error(f"❌ Error predicting stockouts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/{facility_id}")
async def get_facility_alerts(facility_id: str):
    """
    Get stockout alerts for specific facility
    
    Returns only CRITICAL and WARNING items
    """
    try:
        # Load inventory
        inventory = inventory_loader.load_inventory(facility_id)
        
        if inventory.empty:
            return {
                'facility_id': facility_id,
                'alerts': [],
                'message': 'No inventory data for this facility'
            }
        
        # Get alerts
        result = stockout_predictor.get_facility_alerts(inventory, facility_id)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error getting facility alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/low-stock")
async def get_low_stock_items(
    facility_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500)
):
    """
    Get items at or below reorder level
    
    Returns list of items needing restock
    """
    try:
        low_stock = inventory_loader.get_low_stock_items(facility_id)
        
        if low_stock.empty:
            return {
                'items': [],
                'count': 0,
                'message': 'No low stock items found'
            }
        
        # Convert to list
        items = low_stock.head(limit).to_dict('records')
        
        return {
            'items': items,
            'count': len(items),
            'total_low_stock': len(low_stock)
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting low stock items: {e}")
        raise HTTPException(status_code=500, detail=str(e))