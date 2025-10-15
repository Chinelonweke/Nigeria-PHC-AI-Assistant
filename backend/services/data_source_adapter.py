"""
Data Source Adapter
Unified interface for accessing data from S3 or Redshift
Provides seamless switching between data sources
"""

import pandas as pd
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from backend.core.config import settings
from backend.core.logger import get_logger
from backend.services.s3_service import s3_service

logger = get_logger(__name__)


class DataSourceAdapter:
    """
    Adapter for accessing data from S3 or Redshift
    
    Features:
    - Unified interface for both data sources
    - Automatic fallback to S3 if Redshift unavailable
    - Query caching
    - Data validation
    """
    
    def __init__(self):
        """Initialize data source adapter"""
        self.use_redshift = settings.USE_REDSHIFT
        self.source_name = "Redshift" if self.use_redshift else "S3"
        
        # Initialize appropriate data source
        if self.use_redshift:
            self._init_redshift()
        else:
            self._init_s3()
        
        logger.info(f"✅ Data Source Adapter initialized (Source: {self.source_name})")
    
    def _init_s3(self):
        """Initialize S3 data source"""
        self.s3 = s3_service
        logger.info("📦 Using S3 as data source")
    
    def _init_redshift(self):
        """Initialize Redshift connection"""
        try:
            import psycopg2
            
            logger.info("🗄️ Initializing Redshift connection...")
            
            self.redshift_conn = psycopg2.connect(
                host=settings.REDSHIFT_HOST,
                port=settings.REDSHIFT_PORT,
                dbname=settings.REDSHIFT_DATABASE,
                user=settings.REDSHIFT_USER,
                password=settings.REDSHIFT_PASSWORD
            )
            
            logger.info("✅ Redshift connection established")
            
        except Exception as e:
            logger.error(f"❌ Redshift connection failed: {e}")
            logger.warning("⚠️ Falling back to S3")
            self.use_redshift = False
            self.source_name = "S3"
            self._init_s3()
    
    def get_source_name(self) -> str:
        """Get current data source name"""
        return self.source_name
    
    def is_connected(self) -> bool:
        """Check if data source is connected"""
        if self.use_redshift:
            try:
                cursor = self.redshift_conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                return True
            except:
                return False
        else:
            # For S3, check if we can list files
            try:
                files = self.s3.list_files()
                return len(files) > 0
            except:
                return False
    
    # ============================================
    # PATIENTS DATA
    # ============================================
    
    def load_patients(self, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Load patients data
        
        Args:
            limit: Maximum number of rows to return
        
        Returns:
            DataFrame with patient records
        """
        try:
            if self.use_redshift:
                return self._load_patients_redshift(limit)
            else:
                return self._load_patients_s3(limit)
        except Exception as e:
            logger.error(f"❌ Error loading patients: {e}")
            return pd.DataFrame()
    
    def _load_patients_s3(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Load patients from S3"""
        df = self.s3.read_csv_to_dataframe('raw_data/patients_dataset.csv')
        if limit:
            df = df.head(limit)
        return df
    
    def _load_patients_redshift(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Load patients from Redshift"""
        query = f"SELECT * FROM {settings.REDSHIFT_SCHEMA}.patients"
        if limit:
            query += f" LIMIT {limit}"
        return pd.read_sql(query, self.redshift_conn)
    
    # ============================================
    # FACILITIES DATA
    # ============================================
    
    def load_facilities(self, operational_only: bool = False) -> pd.DataFrame:
        """
        Load healthcare facilities data
        
        Args:
            operational_only: Only return operational facilities
        
        Returns:
            DataFrame with facility records
        """
        try:
            if self.use_redshift:
                return self._load_facilities_redshift(operational_only)
            else:
                return self._load_facilities_s3(operational_only)
        except Exception as e:
            logger.error(f"❌ Error loading facilities: {e}")
            return pd.DataFrame()
    
    def _load_facilities_s3(self, operational_only: bool = False) -> pd.DataFrame:
        """Load facilities from S3"""
        df = self.s3.read_csv_to_dataframe('raw_data/Nigeria_phc_3200.csv')
        
        if operational_only and 'operational_status' in df.columns:
            df = df[df['operational_status'] == 'Operational']
        
        return df
    
    def _load_facilities_redshift(self, operational_only: bool = False) -> pd.DataFrame:
        """Load facilities from Redshift"""
        query = f"SELECT * FROM {settings.REDSHIFT_SCHEMA}.facilities"
        
        if operational_only:
            query += " WHERE operational_status = 'Operational'"
        
        return pd.read_sql(query, self.redshift_conn)
    
    # ============================================
    # INVENTORY DATA
    # ============================================
    
    def load_inventory(self, low_stock_only: bool = False) -> pd.DataFrame:
        """
        Load inventory data
        
        Args:
            low_stock_only: Only return items with low stock
        
        Returns:
            DataFrame with inventory records
        """
        try:
            if self.use_redshift:
                return self._load_inventory_redshift(low_stock_only)
            else:
                return self._load_inventory_s3(low_stock_only)
        except Exception as e:
            logger.error(f"❌ Error loading inventory: {e}")
            return pd.DataFrame()
    
    def _load_inventory_s3(self, low_stock_only: bool = False) -> pd.DataFrame:
        """Load inventory from S3"""
        df = self.s3.read_csv_to_dataframe('raw_data/inventory_dataset.csv')
        
        if low_stock_only and 'stock_level' in df.columns and 'reorder_level' in df.columns:
            df = df[df['stock_level'] <= df['reorder_level']]
        
        return df
    
    def _load_inventory_redshift(self, low_stock_only: bool = False) -> pd.DataFrame:
        """Load inventory from Redshift"""
        query = f"SELECT * FROM {settings.REDSHIFT_SCHEMA}.inventory"
        
        if low_stock_only:
            query += " WHERE stock_level <= reorder_level"
        
        return pd.read_sql(query, self.redshift_conn)
    
    # ============================================
    # DISEASE DATA
    # ============================================
    
    def load_diseases(
        self, 
        disease: Optional[str] = None,
        months: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Load disease reports
        
        Args:
            disease: Filter by specific disease
            months: Only return data from last N months
        
        Returns:
            DataFrame with disease records
        """
        try:
            if self.use_redshift:
                return self._load_diseases_redshift(disease, months)
            else:
                return self._load_diseases_s3(disease, months)
        except Exception as e:
            logger.error(f"❌ Error loading diseases: {e}")
            return pd.DataFrame()
    
    def _load_diseases_s3(
        self, 
        disease: Optional[str] = None,
        months: Optional[int] = None
    ) -> pd.DataFrame:
        """Load diseases from S3"""
        df = self.s3.read_csv_to_dataframe('raw_data/disease_report_full.csv')
        
        # Filter by disease
        if disease and 'disease' in df.columns:
            df = df[df['disease'].str.contains(disease, case=False, na=False)]
        
        # Filter by date
        if months and 'report_date' in df.columns:
            cutoff_date = datetime.now() - timedelta(days=months * 30)
            df['report_date'] = pd.to_datetime(df['report_date'], errors='coerce')
            df = df[df['report_date'] >= cutoff_date]
        
        return df
    
    def _load_diseases_redshift(
        self, 
        disease: Optional[str] = None,
        months: Optional[int] = None
    ) -> pd.DataFrame:
        """Load diseases from Redshift"""
        query = f"SELECT * FROM {settings.REDSHIFT_SCHEMA}.diseases WHERE 1=1"
        
        if disease:
            query += f" AND disease ILIKE '%{disease}%'"
        
        if months:
            query += f" AND report_date >= CURRENT_DATE - INTERVAL '{months} months'"
        
        return pd.read_sql(query, self.redshift_conn)
    
    # ============================================
    # HEALTH WORKERS DATA
    # ============================================
    
    def load_workers(self) -> pd.DataFrame:
        """
        Load health workers data
        
        Returns:
            DataFrame with health worker records
        """
        try:
            if self.use_redshift:
                return self._load_workers_redshift()
            else:
                return self._load_workers_s3()
        except Exception as e:
            logger.error(f"❌ Error loading workers: {e}")
            return pd.DataFrame()
    
    def _load_workers_s3(self) -> pd.DataFrame:
        """Load workers from S3"""
        return self.s3.read_csv_to_dataframe('raw_data/health_workers_dataset.csv')
    
    def _load_workers_redshift(self) -> pd.DataFrame:
        """Load workers from Redshift"""
        query = f"SELECT * FROM {settings.REDSHIFT_SCHEMA}.health_workers"
        return pd.read_sql(query, self.redshift_conn)
    
    # ============================================
    # UTILITY METHODS
    # ============================================
    
    def load_all_datasets(self) -> Dict[str, pd.DataFrame]:
        """
        Load all datasets at once
        
        Returns:
            Dictionary with all DataFrames
        """
        logger.info("📦 Loading all datasets...")
        
        return {
            'patients': self.load_patients(),
            'facilities': self.load_facilities(),
            'inventory': self.load_inventory(),
            'diseases': self.load_diseases(),
            'workers': self.load_workers()
        }
    
    def close(self):
        """Close data source connections"""
        if self.use_redshift and hasattr(self, 'redshift_conn'):
            try:
                self.redshift_conn.close()
                logger.info("🔒 Redshift connection closed")
            except:
                pass


# Global instance
_data_source_instance = None


def get_data_source() -> DataSourceAdapter:
    """
    Get global data source adapter instance
    
    Returns:
        DataSourceAdapter instance
    """
    global _data_source_instance
    
    if _data_source_instance is None:
        _data_source_instance = DataSourceAdapter()
    
    return _data_source_instance


# Cleanup on module exit
import atexit

def cleanup():
    """Cleanup function called on exit"""
    global _data_source_instance
    if _data_source_instance:
        _data_source_instance.close()

atexit.register(cleanup)