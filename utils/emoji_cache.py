import time
import aiohttp
from typing import Dict, List, Optional, Any
from utils.logger import setup_logger

logger = setup_logger(__name__)

class EmojiCache:
    """Caches API responses to improve performance and reduce API calls."""
    
    def __init__(self, ttl: int = 3600):
        """
        Initialize the emoji cache.
        
        Args:
            ttl: Time to live for cache entries in seconds (default: 1 hour)
        """
        self.ttl = ttl
        self._emojis_cache: Optional[Dict[str, Any]] = None
        self._emojis_timestamp: float = 0
        self._categories_cache: Optional[List[Dict[str, Any]]] = None
        self._categories_timestamp: float = 0
        self._packs_cache: Optional[List[Dict[str, Any]]] = None
        self._packs_timestamp: float = 0
    
    def _is_expired(self, timestamp: float) -> bool:
        """Check if a cache entry has expired."""
        return (time.time() - timestamp) > self.ttl
    
    async def get_emojis(self, api_url: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get all emojis from cache or API.
        
        Args:
            api_url: Base API URL
            force_refresh: Force refresh from API even if cached
            
        Returns:
            List of emoji dictionaries
        """
        if not force_refresh and self._emojis_cache and not self._is_expired(self._emojis_timestamp):
            logger.debug("Returning emojis from cache")
            return self._emojis_cache
        
        logger.info("Fetching emojis from API")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        emojis = await response.json()
                        self._emojis_cache = emojis
                        self._emojis_timestamp = time.time()
                        logger.info(f"Cached {len(emojis)} emojis")
                        return emojis
                    else:
                        logger.error(f"API request failed with status {response.status}")
                        return self._emojis_cache if self._emojis_cache else []
        except Exception as e:
            logger.error(f"Error fetching emojis: {e}")
            return self._emojis_cache if self._emojis_cache else []
    
    async def get_categories(self, api_url: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get all categories from cache or API.
        
        Args:
            api_url: Base API URL
            force_refresh: Force refresh from API even if cached
            
        Returns:
            List of category dictionaries
        """
        if not force_refresh and self._categories_cache and not self._is_expired(self._categories_timestamp):
            logger.debug("Returning categories from cache")
            return self._categories_cache
        
        logger.info("Fetching categories from API")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{api_url}?request=categories") as response:
                    if response.status == 200:
                        categories = await response.json()
                        self._categories_cache = categories
                        self._categories_timestamp = time.time()
                        logger.info(f"Cached {len(categories)} categories")
                        return categories
                    else:
                        logger.error(f"API request failed with status {response.status}")
                        return self._categories_cache if self._categories_cache else []
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            return self._categories_cache if self._categories_cache else []
    
    async def get_packs(self, api_url: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get all packs from cache or API.
        
        Args:
            api_url: Base API URL
            force_refresh: Force refresh from API even if cached
            
        Returns:
            List of pack dictionaries
        """
        if not force_refresh and self._packs_cache and not self._is_expired(self._packs_timestamp):
            logger.debug("Returning packs from cache")
            return self._packs_cache
        
        logger.info("Fetching packs from API")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{api_url}/packs") as response:
                    if response.status == 200:
                        packs = await response.json()
                        self._packs_cache = packs
                        self._packs_timestamp = time.time()
                        logger.info(f"Cached {len(packs)} packs")
                        return packs
                    else:
                        logger.error(f"API request failed with status {response.status}")
                        return self._packs_cache if self._packs_cache else []
        except Exception as e:
            logger.error(f"Error fetching packs: {e}")
            return self._packs_cache if self._packs_cache else []
    
    def clear_cache(self):
        """Clear all cached data."""
        logger.info("Clearing all caches")
        self._emojis_cache = None
        self._emojis_timestamp = 0
        self._categories_cache = None
        self._categories_timestamp = 0
        self._packs_cache = None
        self._packs_timestamp = 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "emojis": {
                "cached": self._emojis_cache is not None,
                "count": len(self._emojis_cache) if self._emojis_cache else 0,
                "age_seconds": time.time() - self._emojis_timestamp if self._emojis_cache else 0,
                "expired": self._is_expired(self._emojis_timestamp) if self._emojis_cache else True
            },
            "categories": {
                "cached": self._categories_cache is not None,
                "count": len(self._categories_cache) if self._categories_cache else 0,
                "age_seconds": time.time() - self._categories_timestamp if self._categories_cache else 0,
                "expired": self._is_expired(self._categories_timestamp) if self._categories_cache else True
            },
            "packs": {
                "cached": self._packs_cache is not None,
                "count": len(self._packs_cache) if self._packs_cache else 0,
                "age_seconds": time.time() - self._packs_timestamp if self._packs_cache else 0,
                "expired": self._is_expired(self._packs_timestamp) if self._packs_cache else True
            }
        }
