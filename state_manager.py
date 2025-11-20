"""
State management for FoodStream Veggies Bot
Provides persistent state storage with Redis and in-memory fallback
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import timedelta

logger = logging.getLogger(__name__)


class StateManager(ABC):
    """Abstract base class for state management"""
    
    @abstractmethod
    def get_state(self, phone_number: str) -> Optional[Dict]:
        """Get user state"""
        pass
    
    @abstractmethod
    def set_state(self, phone_number: str, state: Dict) -> bool:
        """Set user state"""
        pass
    
    @abstractmethod
    def delete_state(self, phone_number: str) -> bool:
        """Delete user state"""
        pass
    
    @abstractmethod
    def get_last_order(self, phone_number: str) -> Optional[Dict]:
        """Get user's last order"""
        pass
    
    @abstractmethod
    def set_last_order(self, phone_number: str, order: Dict) -> bool:
        """Set user's last order"""
        pass


class RedisStateManager(StateManager):
    """Redis-backed state management"""
    
    def __init__(self, redis_url: str, expiration_hours: int = 24):
        """
        Initialize Redis state manager
        
        Args:
            redis_url: Redis connection URL
            expiration_hours: Hours before state expires
        """
        try:
            import redis
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.expiration = timedelta(hours=expiration_hours)
            
            # Test connection
            self.redis_client.ping()
            logger.info(f"✅ Redis connected: {redis_url}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise
    
    def _state_key(self, phone_number: str) -> str:
        """Generate Redis key for user state"""
        return f"state:{phone_number}"
    
    def _order_key(self, phone_number: str) -> str:
        """Generate Redis key for last order"""
        return f"order:{phone_number}"
    
    def get_state(self, phone_number: str) -> Optional[Dict]:
        """Get user state from Redis"""
        try:
            data = self.redis_client.get(self._state_key(phone_number))
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error reading state from Redis: {e}")
            return None
    
    def set_state(self, phone_number: str, state: Dict) -> bool:
        """Set user state in Redis with expiration"""
        try:
            key = self._state_key(phone_number)
            data = json.dumps(state)
            self.redis_client.setex(key, self.expiration, data)
            return True
        except Exception as e:
            logger.error(f"Error writing state to Redis: {e}")
            return False
    
    def delete_state(self, phone_number: str) -> bool:
        """Delete user state from Redis"""
        try:
            self.redis_client.delete(self._state_key(phone_number))
            return True
        except Exception as e:
            logger.error(f"Error deleting state from Redis: {e}")
            return False
    
    def get_last_order(self, phone_number: str) -> Optional[Dict]:
        """Get user's last order from Redis"""
        try:
            data = self.redis_client.get(self._order_key(phone_number))
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error reading order from Redis: {e}")
            return None
    
    def set_last_order(self, phone_number: str, order: Dict) -> bool:
        """Set user's last order in Redis (expires in 7 days)"""
        try:
            key = self._order_key(phone_number)
            data = json.dumps(order)
            # Orders persist longer than conversation state
            self.redis_client.setex(key, timedelta(days=7), data)
            return True
        except Exception as e:
            logger.error(f"Error writing order to Redis: {e}")
            return False


class InMemoryStateManager(StateManager):
    """In-memory state management (fallback for development)"""
    
    def __init__(self):
        """Initialize in-memory storage"""
        self.states: Dict[str, Dict] = {}
        self.orders: Dict[str, Dict] = {}
        logger.warning("⚠️  Using in-memory state storage - data will be lost on restart!")
    
    def get_state(self, phone_number: str) -> Optional[Dict]:
        """Get user state from memory"""
        return self.states.get(phone_number)
    
    def set_state(self, phone_number: str, state: Dict) -> bool:
        """Set user state in memory"""
        self.states[phone_number] = state
        return True
    
    def delete_state(self, phone_number: str) -> bool:
        """Delete user state from memory"""
        if phone_number in self.states:
            del self.states[phone_number]
        return True
    
    def get_last_order(self, phone_number: str) -> Optional[Dict]:
        """Get user's last order from memory"""
        return self.orders.get(phone_number)
    
    def set_last_order(self, phone_number: str, order: Dict) -> bool:
        """Set user's last order in memory"""
        self.orders[phone_number] = order
        return True


def create_state_manager(redis_enabled: bool = False, redis_url: str = None, 
                         expiration_hours: int = 24) -> StateManager:
    """
    Factory function to create appropriate state manager
    
    Args:
        redis_enabled: Whether to use Redis
        redis_url: Redis connection URL
        expiration_hours: Hours before state expires
    
    Returns:
        StateManager instance (Redis or in-memory)
    """
    if redis_enabled and redis_url:
        try:
            return RedisStateManager(redis_url, expiration_hours)
        except Exception as e:
            logger.warning(f"Failed to initialize Redis, falling back to in-memory: {e}")
            return InMemoryStateManager()
    else:
        return InMemoryStateManager()
