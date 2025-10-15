"""
ML Model Service
Loads and serves predictions from trained ML models
"""

import joblib
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from backend.core.config import settings
from backend.core.logger import get_logger
from backend.services.cache_service import cache_service

logger = get_logger(__name__)


class ModelService:
    """
    Service for ML model inference
    
    Features:
    - Load pickle models
    - Stockout prediction
    - Model validation
    - Result caching
    """
    
    def __init__(self):
        """Initialize model service"""
        self.models = {}
        self.model_metadata = {}
        
        logger.info("✅ Model Service initialized")
    
    def load_model(
        self, 
        model_path: str,
        model_name: str = "stockout_model"
    ) -> bool:
        """
        Load ML model from pickle file
        
        Args:
            model_path: Path to .pkl file
            model_name: Name to reference this model
        
        Returns:
            True if successful
            
        Example:
            >>> model_service = ModelService()
            >>> model_service.load_model('./ml_models/stockout_model.pkl')
            >>> print("Model loaded!")
        """
        try:
            model_path = Path(model_path)
            
            if not model_path.exists():
                logger.error(f"❌ Model file not found: {model_path}")
                return False
            
            logger.info(f"📦 Loading model from: {model_path}")
            
            # Load model using joblib (handles sklearn models well)
            try:
                model = joblib.load(model_path)
            except:
                # Fallback to pickle if joblib fails
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
            
            # Store model
            self.models[model_name] = model
            
            # Store metadata
            self.model_metadata[model_name] = {
                'path': str(model_path),
                'loaded_at': datetime.now(),
                'model_type': type(model).__name__,
                'size_mb': model_path.stat().st_size / (1024 * 1024)
            }
            
            logger.info(f"✅ Model '{model_name}' loaded successfully")
            logger.info(f"   Type: {type(model).__name__}")
            logger.info(f"   Size: {self.model_metadata[model_name]['size_mb']:.2f} MB")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            return False
    
    def predict_stockout(
        self,
        item_id: str,
        facility_id: str,
        current_stock: int,
        reorder_level: int,
        last_restock_date: str,
        daily_usage_rate: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Predict when an item will stock out
        
        Args:
            item_id: Item identifier
            facility_id: Facility identifier
            current_stock: Current stock level
            reorder_level: Reorder threshold
            last_restock_date: Last restock date (YYYY-MM-DD)
            daily_usage_rate: Average daily usage (optional)
        
        Returns:
            Prediction results
            
        Example:
            >>> model_service = ModelService()
            >>> model_service.load_model('./ml_models/stockout_model.pkl')
            >>> result = model_service.predict_stockout(
            ...     item_id='ITPHC_00001',
            ...     facility_id='PHC_00003',
            ...     current_stock=100,
            ...     reorder_level=30,
            ...     last_restock_date='2024-10-01'
            ... )
            >>> print(f"Days until stockout: {result['days_until_stockout']}")
        """
        try:
            logger.info(f"🔮 Predicting stockout for {item_id}")
            
            # Check cache
            cache_key = cache_service.generate_unique_id({
                'item_id': item_id,
                'facility_id': facility_id,
                'current_stock': current_stock,
                'reorder_level': reorder_level
            })
            
            cached_result = cache_service.get(cache_key)
            if cached_result:
                logger.info("✅ Using cached prediction")
                return cached_result
            
            # Check if model is loaded
            if 'stockout_model' not in self.models:
                logger.warning("⚠️ Model not loaded, attempting to load...")
                self.load_model(settings.STOCKOUT_MODEL_PATH)
            
            model = self.models.get('stockout_model')
            
            if model is None:
                logger.error("❌ Model not available")
                return self._fallback_stockout_prediction(
                    current_stock, reorder_level, last_restock_date, daily_usage_rate
                )
            
            # Prepare features for model
            features = self._prepare_stockout_features(
                item_id, facility_id, current_stock, reorder_level,
                last_restock_date, daily_usage_rate
            )
            
            # Make prediction
            prediction = model.predict(features)
            
            # If model predicts probability, get it
            try:
                probability = model.predict_proba(features)[0]
            except:
                probability = None
            
            # Calculate days until stockout
            days_until_stockout = int(prediction[0])
            
            # Calculate stockout date
            stockout_date = datetime.now() + timedelta(days=days_until_stockout)
            
            # Determine urgency
            urgency = self._calculate_urgency(days_until_stockout, current_stock, reorder_level)
            
            result = {
                'item_id': item_id,
                'facility_id': facility_id,
                'current_stock': current_stock,
                'reorder_level': reorder_level,
                'days_until_stockout': days_until_stockout,
                'stockout_date': stockout_date.strftime('%Y-%m-%d'),
                'urgency': urgency,
                'should_reorder': current_stock <= reorder_level or days_until_stockout <= 7,
                'confidence': probability[1] if probability is not None else 0.8,
                'prediction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Cache result
            cache_service.set(cache_key, result, ttl=3600)  # Cache for 1 hour
            
            logger.info(f"✅ Prediction: {days_until_stockout} days until stockout ({urgency})")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Prediction error: {e}")
            # Fallback to simple calculation
            return self._fallback_stockout_prediction(
                current_stock, reorder_level, last_restock_date, daily_usage_rate
            )
    
    def _prepare_stockout_features(
        self,
        item_id: str,
        facility_id: str,
        current_stock: int,
        reorder_level: int,
        last_restock_date: str,
        daily_usage_rate: Optional[float]
    ) -> pd.DataFrame:
        """
        Prepare features for ML model
        
        Note: Adjust these features based on what your ML colleague's model expects
        """
        try:
            # Calculate days since last restock
            last_restock = datetime.strptime(last_restock_date, '%Y-%m-%d')
            days_since_restock = (datetime.now() - last_restock).days
            
            # Estimate daily usage if not provided
            if daily_usage_rate is None:
                # Simple estimation: assume uniform usage since last restock
                if days_since_restock > 0:
                    daily_usage_rate = (current_stock / days_since_restock) * 0.8
                else:
                    daily_usage_rate = 5.0  # Default
            
            # Create feature dictionary
            features = {
                'stock_level': [current_stock],
                'reorder_level': [reorder_level],
                'days_since_restock': [days_since_restock],
                'daily_usage_rate': [daily_usage_rate],
                'stock_to_reorder_ratio': [current_stock / max(reorder_level, 1)],
                'is_below_reorder': [int(current_stock <= reorder_level)],
                'days_of_supply': [current_stock / max(daily_usage_rate, 0.1)]
            }
            
            # Convert to DataFrame
            df = pd.DataFrame(features)
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error preparing features: {e}")
            # Return minimal features
            return pd.DataFrame({
                'stock_level': [current_stock],
                'reorder_level': [reorder_level]
            })
    
    def _fallback_stockout_prediction(
        self,
        current_stock: int,
        reorder_level: int,
        last_restock_date: str,
        daily_usage_rate: Optional[float]
    ) -> Dict[str, Any]:
        """
        Simple fallback prediction when model is unavailable
        Uses basic calculation: days = current_stock / daily_usage_rate
        """
        try:
            logger.info("📊 Using fallback prediction method")
            
            # Estimate daily usage
            if daily_usage_rate is None:
                last_restock = datetime.strptime(last_restock_date, '%Y-%m-%d')
                days_since_restock = (datetime.now() - last_restock).days
                
                if days_since_restock > 0:
                    daily_usage_rate = current_stock / days_since_restock * 0.8
                else:
                    daily_usage_rate = 5.0
            
            # Calculate days until stockout
            days_until_stockout = int(current_stock / max(daily_usage_rate, 0.1))
            
            # Calculate stockout date
            stockout_date = datetime.now() + timedelta(days=days_until_stockout)
            
            # Determine urgency
            urgency = self._calculate_urgency(days_until_stockout, current_stock, reorder_level)
            
            return {
                'days_until_stockout': days_until_stockout,
                'stockout_date': stockout_date.strftime('%Y-%m-%d'),
                'urgency': urgency,
                'should_reorder': current_stock <= reorder_level or days_until_stockout <= 7,
                'confidence': 0.6,  # Lower confidence for fallback
                'method': 'fallback',
                'prediction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"❌ Fallback prediction error: {e}")
            return {
                'days_until_stockout': 30,
                'urgency': 'Low',
                'should_reorder': False,
                'confidence': 0.3,
                'error': str(e)
            }
    
    def _calculate_urgency(
        self,
        days_until_stockout: int,
        current_stock: int,
        reorder_level: int
    ) -> str:
        """
        Calculate urgency level
        
        Returns:
            'Critical', 'High', 'Medium', or 'Low'
        """
        if days_until_stockout <= 3 or current_stock < reorder_level * 0.5:
            return 'Critical'
        elif days_until_stockout <= 7 or current_stock <= reorder_level:
            return 'High'
        elif days_until_stockout <= 14:
            return 'Medium'
        else:
            return 'Low'
    
    def batch_predict_stockouts(
        self,
        inventory_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Predict stockouts for multiple items
        
        Args:
            inventory_data: DataFrame with inventory information
        
        Returns:
            DataFrame with predictions
            
        Example:
            >>> inventory_df = pd.read_csv('inventory.csv')
            >>> predictions = model_service.batch_predict_stockouts(inventory_df)
            >>> critical_items = predictions[predictions['urgency'] == 'Critical']
        """
        try:
            logger.info(f"📦 Batch predicting for {len(inventory_data)} items")
            
            results = []
            
            for idx, row in inventory_data.iterrows():
                try:
                    prediction = self.predict_stockout(
                        item_id=row.get('item_id', f'ITEM_{idx}'),
                        facility_id=row.get('facility_id', 'UNKNOWN'),
                        current_stock=int(row.get('stock_level', 0)),
                        reorder_level=int(row.get('reorder_level', 0)),
                        last_restock_date=row.get('last_restock_date', '2024-01-01'),
                        daily_usage_rate=row.get('daily_usage_rate', None)
                    )
                    
                    results.append(prediction)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error predicting for row {idx}: {e}")
                    continue
            
            results_df = pd.DataFrame(results)
            
            logger.info(f"✅ Batch prediction complete: {len(results)} items")
            logger.info(f"   Critical: {len(results_df[results_df['urgency'] == 'Critical'])}")
            logger.info(f"   High: {len(results_df[results_df['urgency'] == 'High'])}")
            
            return results_df
            
        except Exception as e:
            logger.error(f"❌ Batch prediction error: {e}")
            return pd.DataFrame()
    
    def get_model_info(self, model_name: str = "stockout_model") -> Dict:
        """
        Get information about loaded model
        
        Args:
            model_name: Name of model
        
        Returns:
            Model metadata
        """
        if model_name not in self.models:
            return {'error': 'Model not loaded'}
        
        return self.model_metadata.get(model_name, {})
    
    def is_model_loaded(self, model_name: str = "stockout_model") -> bool:
        """Check if model is loaded"""
        return model_name in self.models


# Global instance
model_service = ModelService()


# Test function
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("MODEL SERVICE TEST")
    print("=" * 60 + "\n")
    
    try:
        service = ModelService()
        
        # Test 1: Load model (will fail if file doesn't exist yet)
        print("📦 Test 1: Load Model")
        model_path = Path(settings.STOCKOUT_MODEL_PATH)
        
        if model_path.exists():
            success = service.load_model(str(model_path))
            print(f"  Model loaded: {success}")
        else:
            print(f"  ⚠️ Model file not found: {model_path}")
            print(f"  📝 Note: You'll receive this from your ML colleague")
        
        # Test 2: Fallback prediction (works without model)
        print("\n🔮 Test 2: Stockout Prediction (Fallback)")
        result = service.predict_stockout(
            item_id='TEST_001',
            facility_id='PHC_00003',
            current_stock=50,
            reorder_level=30,
            last_restock_date='2024-09-01',
            daily_usage_rate=2.5
        )
        
        print(f"  Days until stockout: {result['days_until_stockout']}")
        print(f"  Stockout date: {result['stockout_date']}")
        print(f"  Urgency: {result['urgency']}")
        print(f"  Should reorder: {result['should_reorder']}")
        
        print("\n✅ Tests complete!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
    
    print("\n" + "=" * 60)