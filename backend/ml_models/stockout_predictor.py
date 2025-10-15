"""
Stockout Prediction Model
Predicts when medicines will run out and generates alerts
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import joblib
import os

from backend.core.logger import get_logger

logger = get_logger(__name__)


class StockoutPredictor:
    """
    Predicts stockouts using rule-based and ML approaches
    
    HOW IT WORKS (Simple Version):
    1. Calculate days since last restock
    2. Estimate daily usage rate
    3. Predict days until stockout
    4. Generate alerts if < 14 days
    """
    
    def __init__(self):
        """Initialize the predictor"""
        self.model_path = "backend/ml_models/trained_models/stockout_model.pkl"
        self.critical_threshold_days = 7   # Alert if < 7 days left
        self.warning_threshold_days = 14   # Warn if < 14 days left
        
        logger.info("✅ Stockout Predictor initialized")
    
    def predict_stockout_simple(
        self,
        stock_level: int,
        reorder_level: int,
        last_restock_date: str,
        item_name: str,
        facility_id: str
    ) -> Dict:
        """
        Simple rule-based stockout prediction
        
        Args:
            stock_level: Current stock quantity
            reorder_level: Minimum safe stock
            last_restock_date: Date of last refill (YYYY-MM-DD)
            item_name: Medicine name
            facility_id: PHC facility ID
            
        Returns:
            Prediction dict with alert level and days remaining
            
        EXPLANATION:
        - If stock < reorder_level: CRITICAL (reorder NOW!)
        - If stock < reorder_level * 1.5: WARNING (will hit reorder soon)
        - Otherwise: OK
        """
        try:
            # Convert date string to datetime
            last_restock = pd.to_datetime(last_restock_date)
            today = datetime.now()
            
            # Calculate days since last restock
            days_since_restock = (today - last_restock).days
            
            # Estimate daily usage (simple approach)
            # Assumption: If it took X days to go from full stock to current level
            if days_since_restock > 0:
                # We don't know "full stock", so we estimate
                # Assume reorder_level * 3 was full stock (reasonable assumption)
                estimated_full_stock = reorder_level * 3
                stock_consumed = estimated_full_stock - stock_level
                daily_usage = stock_consumed / days_since_restock
            else:
                # Just restocked, assume moderate usage
                daily_usage = reorder_level / 30  # Will last 30 days
            
            # Predict days until stockout
            if daily_usage > 0:
                days_until_stockout = stock_level / daily_usage
                days_until_reorder = (stock_level - reorder_level) / daily_usage
            else:
                days_until_stockout = 999  # No usage, won't run out
                days_until_reorder = 999
            
            # Determine alert level
            if stock_level <= reorder_level:
                alert_level = "CRITICAL"
                priority = 1
                message = f"⚠️ URGENT: {item_name} at reorder level! Order immediately!"
            elif days_until_reorder <= self.critical_threshold_days:
                alert_level = "WARNING"
                priority = 2
                message = f"⚡ WARNING: {item_name} will hit reorder level in {int(days_until_reorder)} days"
            elif days_until_reorder <= self.warning_threshold_days:
                alert_level = "ATTENTION"
                priority = 3
                message = f"📌 ATTENTION: {item_name} running low, {int(days_until_reorder)} days until reorder"
            else:
                alert_level = "OK"
                priority = 4
                message = f"✅ {item_name} stock level is adequate"
            
            return {
                'item_name': item_name,
                'facility_id': facility_id,
                'current_stock': int(stock_level),
                'reorder_level': int(reorder_level),
                'days_until_stockout': round(days_until_stockout, 1),
                'days_until_reorder': round(days_until_reorder, 1),
                'daily_usage_estimate': round(daily_usage, 2),
                'alert_level': alert_level,
                'priority': priority,
                'message': message,
                'recommended_order_quantity': int(reorder_level * 2),  # Order 2x reorder level
                'prediction_date': today.strftime('%Y-%m-%d'),
                'confidence': 'Medium'  # Simple model = medium confidence
            }
            
        except Exception as e:
            logger.error(f"❌ Error predicting stockout: {e}")
            return {
                'error': str(e),
                'alert_level': 'UNKNOWN'
            }
    
    def batch_predict(self, inventory_df: pd.DataFrame) -> List[Dict]:
        """
        Predict stockouts for entire inventory
        
        Args:
            inventory_df: DataFrame with inventory data
            
        Returns:
            List of predictions for all items
        """
        try:
            logger.info(f"📊 Running batch stockout prediction for {len(inventory_df)} items...")
            
            predictions = []
            
            for idx, row in inventory_df.iterrows():
                prediction = self.predict_stockout_simple(
                    stock_level=row['stock_level'],
                    reorder_level=row['reorder_level'],
                    last_restock_date=row['last_restock_date'],
                    item_name=row['item_name'],
                    facility_id=row['facility_id']
                )
                predictions.append(prediction)
            
            # Sort by priority (critical first)
            predictions.sort(key=lambda x: x.get('priority', 999))
            
            # Statistics
            critical_count = len([p for p in predictions if p['alert_level'] == 'CRITICAL'])
            warning_count = len([p for p in predictions if p['alert_level'] == 'WARNING'])
            
            logger.info(f"✅ Prediction complete:")
            logger.info(f"   🔴 CRITICAL: {critical_count} items")
            logger.info(f"   🟡 WARNING: {warning_count} items")
            
            return predictions
            
        except Exception as e:
            logger.error(f"❌ Error in batch prediction: {e}")
            return []
    
    def get_facility_alerts(
        self,
        inventory_df: pd.DataFrame,
        facility_id: str
    ) -> Dict:
        """
        Get stockout alerts for specific facility
        
        Returns summary of critical items needing attention
        """
        try:
            # Filter for facility
            facility_inventory = inventory_df[
                inventory_df['facility_id'] == facility_id
            ]
            
            # Run predictions
            predictions = self.batch_predict(facility_inventory)
            
            # Filter alerts (only CRITICAL and WARNING)
            alerts = [
                p for p in predictions 
                if p['alert_level'] in ['CRITICAL', 'WARNING']
            ]
            
            return {
                'facility_id': facility_id,
                'total_items': len(predictions),
                'alert_count': len(alerts),
                'critical_count': len([a for a in alerts if a['alert_level'] == 'CRITICAL']),
                'warning_count': len([a for a in alerts if a['alert_level'] == 'WARNING']),
                'alerts': alerts,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting facility alerts: {e}")
            return {'error': str(e)}


# Global instance
stockout_predictor = StockoutPredictor()