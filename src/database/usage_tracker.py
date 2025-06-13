"""
User usage tracking for API cost management.
"""
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from ..utils.logging_utils import setup_logger
from ..config.settings import settings

logger = setup_logger("UsageTracker")

@dataclass
class UsageRecord:
    """Represents a single usage record."""
    user_id: str
    timestamp: datetime
    api_service: str  # 'groq', 'coingecko', etc.
    tokens_used: int
    estimated_cost: float
    request_type: str  # 'analysis', 'chart', etc.

class UsageTracker:
    """Tracks API usage per user for cost management."""
    
    def __init__(self, db_path: str = None):
        """Initialize the usage tracker."""
        if db_path is None:
            # Create data directory in project root
            project_root = Path(__file__).parent.parent.parent
            data_dir = project_root / "data"
            data_dir.mkdir(exist_ok=True)
            self.db_path = str(data_dir / "usage_tracker.db")
        else:
            self.db_path = db_path
            
        self._init_database()
        logger.info(f"UsageTracker initialized with database: {self.db_path}")
    
    def _init_database(self):
        """Initialize the SQLite database."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS usage_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        api_service TEXT NOT NULL,
                        tokens_used INTEGER DEFAULT 0,
                        estimated_cost REAL DEFAULT 0.0,
                        request_type TEXT NOT NULL,
                        metadata TEXT DEFAULT '{}'
                    )
                """)                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_limits (
                        user_id TEXT PRIMARY KEY,
                        monthly_limit REAL DEFAULT 10.0,
                        daily_limit REAL DEFAULT 2.0,
                        requests_per_hour INTEGER DEFAULT 20,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_timestamp 
                    ON usage_records(user_id, timestamp)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_limits 
                    ON user_limits(user_id)
                """)
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def record_usage(self, user_id: str, api_service: str, tokens_used: int, 
                     estimated_cost: float, request_type: str, metadata: Dict = None) -> bool:
        """Record API usage for a user."""
        try:
            metadata = metadata or {}
            timestamp = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO usage_records 
                    (user_id, timestamp, api_service, tokens_used, estimated_cost, request_type, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (user_id, timestamp, api_service, tokens_used, estimated_cost, request_type, json.dumps(metadata)))
                
                conn.commit()
                
            logger.debug(f"Recorded usage for user {user_id}: {api_service} - ${estimated_cost:.4f}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording usage: {e}")
            return False
    
    def get_user_usage(self, user_id: str, days: int = 30) -> Dict[str, Dict[str, float]]:
        """Get user usage statistics for the specified period."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        api_service,
                        SUM(tokens_used) as total_tokens,
                        SUM(estimated_cost) as total_cost,
                        COUNT(*) as request_count
                    FROM usage_records 
                    WHERE user_id = ? AND timestamp >= ?
                    GROUP BY api_service
                """, (user_id, start_date))
                
                results = cursor.fetchall()
                
            usage_stats = {}
            for api_service, tokens, cost, count in results:
                usage_stats[api_service] = {
                    'tokens': tokens or 0,
                    'cost': cost or 0.0,
                    'requests': count or 0
                }
            
            return usage_stats
            
        except Exception as e:
            logger.error(f"Error getting user usage: {e}")
            return {}
    
    def check_user_limits(self, user_id: str) -> Dict[str, any]:
        """Check if user is within their usage limits."""
        try:
            # Get user limits
            limits = self.get_user_limits(user_id)
            
            # Get current usage
            monthly_usage = self.get_user_usage(user_id, days=30)
            daily_usage = self.get_user_usage(user_id, days=1)
            hourly_requests = self.get_hourly_request_count(user_id)
            
            # Calculate totals
            monthly_cost = sum(service['cost'] for service in monthly_usage.values())
            daily_cost = sum(service['cost'] for service in daily_usage.values())
            
            return {
                'within_limits': (
                    monthly_cost <= limits['monthly_limit'] and
                    daily_cost <= limits['daily_limit'] and
                    hourly_requests <= limits['requests_per_hour']
                ),
                'monthly_usage': monthly_cost,
                'monthly_limit': limits['monthly_limit'],
                'daily_usage': daily_cost,
                'daily_limit': limits['daily_limit'],
                'hourly_requests': hourly_requests,                'hourly_limit': limits['requests_per_hour']
            }
            
        except Exception as e:
            logger.error(f"Error checking user limits: {e}")
            return {'within_limits': False}
    
    def get_user_limits(self, user_id: str) -> Dict[str, any]:
        """Get user limits, creating default if not exists."""
        try:
            with sqlite3.connect(self.db_path) as conn:                cursor = conn.execute("""
                    SELECT monthly_limit, daily_limit, requests_per_hour
                    FROM user_limits WHERE user_id = ?
                """, (user_id,))
                
            result = cursor.fetchone()
                
            if result:
                    return {
                        'monthly_limit': result[0],
                        'daily_limit': result[1],
                        'requests_per_hour': result[2]
                    }
            else:
                    # Create default limits
                    return self.create_default_limits(user_id)
                    
        except Exception as e:
            logger.error(f"Error getting user limits: {e}")
            return self.create_default_limits(user_id)
    
    def create_default_limits(self, user_id: str) -> Dict[str, any]:
        """Create default limits for a new user - Uniform limits for all users."""
        try:
            # Uniform limits for all users
            default_limits = {
                'monthly_limit': getattr(settings, 'DEFAULT_MONTHLY_LIMIT', 10.0),
                'daily_limit': getattr(settings, 'DEFAULT_DAILY_LIMIT', 2.0),
                'requests_per_hour': getattr(settings, 'DEFAULT_HOURLY_REQUESTS', 20)
            }
            
            timestamp = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO user_limits 
                    (user_id, monthly_limit, daily_limit, requests_per_hour, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, default_limits['monthly_limit'], default_limits['daily_limit'],
                      default_limits['requests_per_hour'], timestamp, timestamp))
                
                conn.commit()
                
            logger.info(f"Created default limits for user {user_id}")
            return default_limits
            
        except Exception as e:
            logger.error(f"Error creating default limits: {e}")
            return {
                'monthly_limit': 10.0,
                'daily_limit': 2.0,
                'requests_per_hour': 20
            }
    
    def get_hourly_request_count(self, user_id: str) -> int:
        """Get number of requests in the last hour."""
        try:
            one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM usage_records 
                    WHERE user_id = ? AND timestamp >= ?
                """, (user_id, one_hour_ago))
                
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"Error getting hourly request count: {e}")
            return 0
    def update_user_limits(self, user_id: str, monthly_limit: float = None, 
                          daily_limit: float = None, requests_per_hour: int = None) -> bool:
        """Update user limits."""
        try:
            current_limits = self.get_user_limits(user_id)
            
            # Update only provided values
            if monthly_limit is not None:
                current_limits['monthly_limit'] = monthly_limit
            if daily_limit is not None:
                current_limits['daily_limit'] = daily_limit
            if requests_per_hour is not None:
                current_limits['requests_per_hour'] = requests_per_hour
            
            timestamp = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                # Get existing created_at timestamp
                cursor = conn.execute("""
                    SELECT created_at FROM user_limits WHERE user_id = ?
                """, (user_id,))
                result = cursor.fetchone()
                created_at = result[0] if result else timestamp
                
                conn.execute("""
                    INSERT OR REPLACE INTO user_limits 
                    (user_id, monthly_limit, daily_limit, requests_per_hour, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, current_limits['monthly_limit'], current_limits['daily_limit'],
                      current_limits['requests_per_hour'], created_at, timestamp))
                
                conn.commit()
                
            logger.info(f"Updated limits for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user limits: {e}")
            return False
    
    def get_top_users_by_usage(self, days: int = 30, limit: int = 10) -> List[Tuple[str, float]]:
        """Get top users by usage cost."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT user_id, SUM(estimated_cost) as total_cost
                    FROM usage_records 
                    WHERE timestamp >= ?
                    GROUP BY user_id
                    ORDER BY total_cost DESC
                    LIMIT ?
                """, (start_date, limit))
                
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"Error getting top users: {e}")
            return []
    
    def get_usage_stats(self, days: int = 30) -> Dict[str, any]:
        """Get overall usage statistics."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(DISTINCT user_id) as unique_users,
                        COUNT(*) as total_requests,
                        SUM(estimated_cost) as total_cost,
                        AVG(estimated_cost) as avg_cost_per_request
                    FROM usage_records 
                    WHERE timestamp >= ?
                """, (start_date,))
                
                result = cursor.fetchone()
                
                if result:
                    return {
                        'unique_users': result[0] or 0,
                        'total_requests': result[1] or 0,
                        'total_cost': result[2] or 0.0,
                        'avg_cost_per_request': result[3] or 0.0,
                        'period_days': days
                    }
                
            return {
                'unique_users': 0,
                'total_requests': 0,
                'total_cost': 0.0,
                'avg_cost_per_request': 0.0,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error getting usage stats: {e}")
            return {}
