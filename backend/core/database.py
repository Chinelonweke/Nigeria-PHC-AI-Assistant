"""
Database Service - DynamoDB
Handles all database operations including chat, logs, embeddings, and deduplication
"""

import boto3
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime
from typing import Dict, List, Optional, Any
from decimal import Decimal
import json
import uuid

from backend.core.config import get_aws_config, settings
from backend.core.logger import get_logger
from backend.services.deduplication_service import deduplication_service

logger = get_logger(__name__)


# ---------------- Helper Converters ---------------- #

def float_to_decimal(obj):
    """Convert floats to Decimal for DynamoDB"""
    if isinstance(obj, dict):
        return {k: float_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [float_to_decimal(item) for item in obj]
    elif isinstance(obj, float):
        return Decimal(str(obj))
    return obj


def decimal_to_float(obj):
    """Convert Decimal to float for JSON serialization"""
    if isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj


# ---------------- Database Service ---------------- #

class DatabaseService:
    """
    Service for DynamoDB operations
    Features:
    - Chat message storage with deduplication
    - System logs
    - Embeddings
    """

    def __init__(self):
        """Initialize DynamoDB client"""
        try:
            aws_config = get_aws_config()
            self.dynamodb = boto3.resource('dynamodb', **aws_config)

            # Table names
            self.chat_table_name = settings.DYNAMODB_CHAT_TABLE
            self.logs_table_name = settings.DYNAMODB_LOGS_TABLE
            self.embeddings_table_name = settings.DYNAMODB_EMBEDDINGS_TABLE

            # Table references
            self.chat_table = self.dynamodb.Table(self.chat_table_name)
            self.logs_table = self.dynamodb.Table(self.logs_table_name)
            self.embeddings_table = self.dynamodb.Table(self.embeddings_table_name)

            logger.info("✅ Database Service initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Database Service: {e}")
            raise

    # ---------------- Table Creation ---------------- #

    def create_tables(self):
        """Create DynamoDB tables if they don't exist"""
        try:
            self._create_chat_table()
            self._create_logs_table()
            self._create_embeddings_table()
            logger.info("✅ All tables created/verified")
        except Exception as e:
            logger.error(f"❌ Error creating tables: {e}")

    def _create_chat_table(self):
        try:
            table = self.dynamodb.create_table(
                TableName=self.chat_table_name,
                KeySchema=[
                    {'AttributeName': 'message_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'message_id', 'AttributeType': 'S'},
                    {'AttributeName': 'created_at', 'AttributeType': 'N'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            table.wait_until_exists()
            logger.info(f"✅ Created table: {self.chat_table_name}")
        except self.dynamodb.meta.client.exceptions.ResourceInUseException:
            logger.info(f"ℹ️ Table already exists: {self.chat_table_name}")
        except Exception as e:
            logger.error(f"❌ Error creating chat table: {e}")

    def _create_logs_table(self):
        try:
            table = self.dynamodb.create_table(
                TableName=self.logs_table_name,
                KeySchema=[
                    {'AttributeName': 'log_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'log_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            table.wait_until_exists()
            logger.info(f"✅ Created table: {self.logs_table_name}")
        except self.dynamodb.meta.client.exceptions.ResourceInUseException:
            logger.info(f"ℹ️ Table already exists: {self.logs_table_name}")
        except Exception as e:
            logger.error(f"❌ Error creating logs table: {e}")

    def _create_embeddings_table(self):
        try:
            table = self.dynamodb.create_table(
                TableName=self.embeddings_table_name,
                KeySchema=[
                    {'AttributeName': 'embedding_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'embedding_id', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            table.wait_until_exists()
            logger.info(f"✅ Created table: {self.embeddings_table_name}")
        except self.dynamodb.meta.client.exceptions.ResourceInUseException:
            logger.info(f"ℹ️ Table already exists: {self.embeddings_table_name}")
        except Exception as e:
            logger.error(f"❌ Error creating embeddings table: {e}")

    # ---------------- Chat Storage (with Deduplication) ---------------- #

    def save_chat_message(
        self,
        user_id: str,
        message: str,
        response: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Save chat message with deduplication.
        Returns the deterministic message_id.
        """
        try:
            # Use deduplication service to prevent duplicates
            content = {'user_id': user_id, 'message': message}
            message_id, is_new = deduplication_service.get_or_create_query_id(content)

            if not is_new:
                logger.info("🔄 Duplicate chat detected, not storing again.")
                return message_id

            timestamp = datetime.now()
            item = {
                'message_id': message_id,
                'user_id': user_id,
                'message': message,
                'response': response,
                'metadata': float_to_decimal(metadata) if metadata else {},
                'created_at': int(timestamp.timestamp()),
                'timestamp': timestamp.isoformat()
            }

            self.chat_table.put_item(Item=item)
            logger.info(f"✅ Chat message saved: {message_id[:8]}...")
            return message_id

        except Exception as e:
            logger.error(f"❌ Error saving chat message: {e}")
            return "error"

    def get_chat_history(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Retrieve chat history for a user"""
        try:
            response = self.chat_table.scan(
                FilterExpression=Attr('user_id').eq(user_id),
                Limit=limit
            )
            items = sorted(response.get('Items', []), key=lambda x: x.get('created_at', 0))
            return decimal_to_float(items)
        except Exception as e:
            logger.error(f"❌ Error retrieving chat history: {e}")
            return []

    # ---------------- Logging ---------------- #

    def save_log(self, log_type: str, message: str, data: Optional[Dict] = None) -> bool:
        """Save system logs"""
        try:
            item = {
                'log_id': str(uuid.uuid4()),
                'timestamp': datetime.now().isoformat(),
                'log_type': log_type,
                'message': message,
                'data': float_to_decimal(data) if data else {}
            }
            self.logs_table.put_item(Item=item)
            logger.debug(f"📝 Saved log: {log_type}")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving log: {e}")
            return False

    # ---------------- Embeddings ---------------- #

    def save_embedding(self, embedding_id: str, content: str, embedding_vector: List[float], metadata: Optional[Dict] = None) -> bool:
        """Save unique embedding"""
        try:
            if self.embeddings_table.get_item(Key={'embedding_id': embedding_id}).get('Item'):
                logger.debug(f"ℹ️ Embedding already exists: {embedding_id[:8]}...")
                return True

            item = {
                'embedding_id': embedding_id,
                'content': content,
                'embedding': float_to_decimal(embedding_vector),
                'metadata': float_to_decimal(metadata) if metadata else {},
                'created_at': datetime.now().isoformat()
            }
            self.embeddings_table.put_item(Item=item)
            logger.info(f"💾 Embedding saved: {embedding_id[:8]}...")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving embedding: {e}")
            return False


# ---------------- Global Instance ---------------- #

db_service = DatabaseService()


# ---------------- Test Runner ---------------- #

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("DATABASE SERVICE TEST")
    print("=" * 60 + "\n")

    try:
        db = DatabaseService()
        print("📋 Test 1: Create Tables")
        create = input("Create tables in AWS DynamoDB? (yes/no): ").strip().lower()
        if create == "yes":
            db.create_tables()
            print("✅ Tables created!")
        else:
            print("⏭️ Skipped table creation")
        print("\n✅ Database Service ready!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")

    print("\n" + "=" * 60)
