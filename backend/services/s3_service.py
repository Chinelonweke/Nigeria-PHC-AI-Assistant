"""
AWS S3 Service
Handles all S3 operations - downloading datasets, uploading files
"""

import boto3
import pandas as pd
import io
from typing import Optional, List
from pathlib import Path
from botocore.exceptions import ClientError, NoCredentialsError

from backend.core.config import get_aws_config, settings
from backend.core.logger import get_logger

logger = get_logger(__name__)


class S3Service:
    """
    Service for AWS S3 operations
    
    Features:
    - Download CSV files from data team's bucket
    - List files in bucket
    - Upload files (for logs, models, etc.)
    - Cache downloaded files to avoid re-downloading
    """
    
    def __init__(self):
        """Initialize S3 client with credentials from .env"""
        try:
            aws_config = get_aws_config()
            self.s3_client = boto3.client('s3', **aws_config)
            self.bucket_name = settings.S3_BUCKET_NAME
            self.region = settings.AWS_REGION
            
            # Local cache directory
            self.cache_dir = Path("data/cache")
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"✅ S3 Service initialized - Bucket: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize S3 Service: {e}")
            raise
    
    def list_files(self, prefix: str = "") -> List[str]:
        """
        List all files in the S3 bucket
        
        Args:
            prefix: Filter files by prefix (folder path)
        
        Returns:
            List of file names
            
        Example:
            >>> s3 = S3Service()
            >>> files = s3.list_files()
            >>> print(files)
            ['patients_dataset.csv', 'inventory_dataset.csv', ...]
        """
        try:
            logger.info(f"📋 Listing files in s3://{self.bucket_name}/{prefix}")
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                logger.warning("⚠️ No files found in bucket")
                return []
            
            files = [obj['Key'] for obj in response['Contents']]
            logger.info(f"✅ Found {len(files)} files")
            
            return files
            
        except ClientError as e:
            logger.error(f"❌ Error listing files: {e}")
            return []
        except NoCredentialsError:
            logger.error("❌ AWS credentials not found. Check your .env file")
            return []
    
    def download_file(
        self, 
        s3_key: str, 
        local_path: Optional[str] = None,
        use_cache: bool = True
    ) -> str:
        """
        Download file from S3 to local storage
        
        Args:
            s3_key: File name in S3 (e.g., 'patients_dataset.csv')
            local_path: Where to save locally (optional)
            use_cache: Use cached file if exists
        
        Returns:
            Path to downloaded file
            
        Example:
            >>> s3 = S3Service()
            >>> path = s3.download_file('patients_dataset.csv')
            >>> print(path)
            'data/cache/patients_dataset.csv'
        """
        try:
            # Use cache directory if no local path specified
            if local_path is None:
                local_path = self.cache_dir / s3_key
            else:
                local_path = Path(local_path)
            
            # Check cache first
            if use_cache and local_path.exists():
                logger.info(f"✅ Using cached file: {local_path}")
                return str(local_path)
            
            # Download from S3
            logger.info(f"⬇️ Downloading s3://{self.bucket_name}/{s3_key}")
            
            # Create parent directories if needed
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.s3_client.download_file(
                Bucket=self.bucket_name,
                Key=s3_key,
                Filename=str(local_path)
            )
            
            logger.info(f"✅ Downloaded to {local_path}")
            return str(local_path)
            
        except ClientError as e:
            logger.error(f"❌ Error downloading {s3_key}: {e}")
            raise
        except NoCredentialsError:
            logger.error("❌ AWS credentials not found")
            raise
    
    def read_csv_to_dataframe(
        self, 
        s3_key: str,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Download CSV from S3 and load into pandas DataFrame
        
        Args:
            s3_key: CSV file name in S3
            use_cache: Use cached file if exists
        
        Returns:
            pandas DataFrame
            
        Example:
            >>> s3 = S3Service()
            >>> df = s3.read_csv_to_dataframe('patients_dataset.csv')
            >>> print(df.head())
        """
        try:
            logger.info(f"📊 Loading CSV: {s3_key}")
            
            # Download file first
            local_path = self.download_file(s3_key, use_cache=use_cache)
            
            # Read into DataFrame
            df = pd.read_csv(local_path)
            logger.info(f"✅ Loaded {len(df)} rows, {len(df.columns)} columns")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error reading CSV {s3_key}: {e}")
            raise
    
    def read_csv_from_memory(self, s3_key: str) -> pd.DataFrame:
        """
        Read CSV directly into memory without saving to disk
        (Useful for small files or when disk space is limited)
        
        Args:
            s3_key: CSV file name in S3
        
        Returns:
            pandas DataFrame
            
        Example:
            >>> s3 = S3Service()
            >>> df = s3.read_csv_from_memory('small_file.csv')
        """
        try:
            logger.info(f"📊 Loading CSV to memory: {s3_key}")
            
            # Get object from S3
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            # Read directly into DataFrame
            df = pd.read_csv(io.BytesIO(response['Body'].read()))
            logger.info(f"✅ Loaded {len(df)} rows from memory")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error reading CSV from memory: {e}")
            raise
    
    def upload_file(
        self, 
        local_path: str, 
        s3_key: Optional[str] = None
    ) -> bool:
        """
        Upload file to S3 bucket
        
        Args:
            local_path: Path to local file
            s3_key: Destination key in S3 (optional, uses filename if None)
        
        Returns:
            True if successful, False otherwise
            
        Example:
            >>> s3 = S3Service()
            >>> success = s3.upload_file('model.pkl', 'models/stockout_model.pkl')
        """
        try:
            local_path = Path(local_path)
            
            if not local_path.exists():
                logger.error(f"❌ File not found: {local_path}")
                return False
            
            # Use filename as S3 key if not provided
            if s3_key is None:
                s3_key = local_path.name
            
            logger.info(f"⬆️ Uploading to s3://{self.bucket_name}/{s3_key}")
            
            self.s3_client.upload_file(
                Filename=str(local_path),
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            logger.info(f"✅ Upload successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error uploading file: {e}")
            return False
    
    def file_exists(self, s3_key: str) -> bool:
        """
        Check if file exists in S3 bucket
        
        Args:
            s3_key: File name in S3
        
        Returns:
            True if exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False
    
    def get_all_datasets(self) -> dict:
        """
        Load all 5 datasets from S3
        
        Returns:
            Dictionary with all DataFrames
            
        Example:
            >>> s3 = S3Service()
            >>> datasets = s3.get_all_datasets()
            >>> print(datasets.keys())
            dict_keys(['patients', 'facilities', 'inventory', 'diseases', 'workers'])
        """
        logger.info("📦 Loading all datasets...")
        
        datasets = {}
        
        try:
            # Dataset file names
            files = {
                'patients': 'patients_dataset.csv',
                'facilities': 'Nigeria_phc_3200.csv',
                'inventory': 'inventory_dataset.csv',
                'diseases': 'disease_report_full.csv',
                'workers': 'health_workers_dataset.csv'
            }
            
            for name, filename in files.items():
                logger.info(f"Loading {name}...")
                datasets[name] = self.read_csv_to_dataframe(filename)
            
            logger.info(f"✅ All {len(datasets)} datasets loaded successfully")
            return datasets
            
        except Exception as e:
            logger.error(f"❌ Error loading datasets: {e}")
            raise


# Create global instance
s3_service = S3Service()


# Test function
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("S3 SERVICE TEST")
    print("=" * 60 + "\n")
    
    try:
        # Initialize service
        s3 = S3Service()
        
        # Test 1: List files
        print("\n📋 Test 1: List files in bucket")
        files = s3.list_files()
        for f in files:
            print(f"  - {f}")
        
        # Test 2: Download a file
        print("\n📥 Test 2: Download patients dataset")
        path = s3.download_file('patients_dataset.csv')
        print(f"  Downloaded to: {path}")
        
        # Test 3: Load CSV to DataFrame
        print("\n📊 Test 3: Load CSV to DataFrame")
        df = s3.read_csv_to_dataframe('patients_dataset.csv')
        print(f"  Shape: {df.shape}")
        print(f"  Columns: {list(df.columns)}")
        print(f"  First few rows:")
        print(df.head(3))
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
    
    print("\n" + "=" * 60)