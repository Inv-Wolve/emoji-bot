import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

class EmojiFilter:
    """Filters and sorts emojis based on quality metrics and content filters."""
    
    def __init__(self, config_manager):
        """
        Initialize the emoji filter.
        
        Args:
            config_manager: ConfigManager instance for accessing settings
        """
        self.config = config_manager
        self.adult_keywords = self._load_adult_keywords()
    
    def _load_adult_keywords(self) -> List[str]:
        """Load adult content keywords from JSON file."""
        try:
            keywords_file = Path("adult_keywords.json")
            if keywords_file.exists():
                with open(keywords_file, 'r') as f:
                    keywords = json.load(f)
                    logger.info(f"Loaded {len(keywords)} adult keywords")
                    return [k.lower() for k in keywords]
            else:
                logger.warning("adult_keywords.json not found")
                return []
        except Exception as e:
            logger.error(f"Error loading adult keywords: {e}")
            return []
    
    def _contains_adult_content(self, emoji: Dict[str, Any]) -> bool:
        """
        Check if emoji contains adult content.
        
        Args:
            emoji: Emoji dictionary from API
            
        Returns:
            True if adult content detected
        """
        if not self.adult_keywords:
            return False
        
        # Check title and description
        title = emoji.get("title", "").lower()
        description = emoji.get("description", "").lower()
        slug = emoji.get("slug", "").lower()
        
        for keyword in self.adult_keywords:
            if keyword in title or keyword in description or keyword in slug:
                logger.debug(f"Adult content detected in emoji: {title} (keyword: {keyword})")
                return True
        
        return False
    
    def _is_quality_emoji(self, emoji: Dict[str, Any]) -> bool:
        """
        Check if emoji meets quality standards.
        
        Args:
            emoji: Emoji dictionary from API
            
        Returns:
            True if emoji meets quality standards
        """
        # Check minimum favorites
        min_faves = self.config.get("emoji_quality.min_favorites", 0)
        faves = emoji.get("faves", 0)
        if faves < min_faves:
            return False
        
        # Check file size (if available)
        filesize = emoji.get("filesize", 0)
        if filesize > 0:
            min_size = self.config.get("emoji_quality.min_file_size", 100)
            max_size = self.config.get("emoji_quality.max_file_size", 256000)
            if filesize < min_size or filesize > max_size:
                logger.debug(f"Emoji {emoji.get('title')} rejected: filesize {filesize}")
                return False
        
        # Check for valid title (not gibberish)
        title = emoji.get("title", "")
        if len(title) < 2 or len(title) > 100:
            return False
        
        # Check if title is mostly alphanumeric or underscores
        if not re.match(r'^[a-zA-Z0-9_\-\s]+$', title):
            # Allow some special characters but reject if too many
            special_chars = len(re.findall(r'[^a-zA-Z0-9_\-\s]', title))
            if special_chars > len(title) * 0.3:  # More than 30% special chars
                logger.debug(f"Emoji {title} rejected: too many special characters")
                return False
        
        return True
    
    def filter_emojis(
        self,
        emojis: List[Dict[str, Any]],
        category: Optional[int] = None,
        include_animated: bool = True,
        adult_filter: bool = True,
        min_favorites: Optional[int] = None,
        search_query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter emojis based on various criteria.
        
        Args:
            emojis: List of emoji dictionaries
            category: Filter by category ID
            include_animated: Include animated (GIF) emojis
            adult_filter: Filter out adult content
            min_favorites: Minimum number of favorites
            search_query: Search query to match against title/description
            
        Returns:
            Filtered list of emojis
        """
        filtered = []
        
        for emoji in emojis:
            # Category filter
            if category is not None and emoji.get("category") != category:
                continue
            
            # Animated filter
            if not include_animated and emoji.get("image", "").endswith(".gif"):
                continue
            
            # Adult content filter
            if adult_filter and self.config.get("emoji_quality.adult_filter_enabled", True):
                if self._contains_adult_content(emoji):
                    continue
            
            # Quality filter
            if not self._is_quality_emoji(emoji):
                continue
            
            # Favorites filter
            if min_favorites is not None:
                if emoji.get("faves", 0) < min_favorites:
                    continue
            
            # Search query filter
            if search_query:
                query_lower = search_query.lower()
                title = emoji.get("title", "").lower()
                description = emoji.get("description", "").lower()
                if query_lower not in title and query_lower not in description:
                    continue
            
            filtered.append(emoji)
        
        logger.info(f"Filtered {len(emojis)} emojis to {len(filtered)} emojis")
        return filtered
    
    def sort_emojis(
        self,
        emojis: List[Dict[str, Any]],
        sort_by: str = "favorites"
    ) -> List[Dict[str, Any]]:
        """
        Sort emojis by specified criteria.
        
        Args:
            emojis: List of emoji dictionaries
            sort_by: Sort criteria ('favorites', 'title', 'random', 'recent')
            
        Returns:
            Sorted list of emojis
        """
        if sort_by == "favorites":
            return sorted(emojis, key=lambda e: e.get("faves", 0), reverse=True)
        elif sort_by == "title":
            return sorted(emojis, key=lambda e: e.get("title", "").lower())
        elif sort_by == "recent":
            return sorted(emojis, key=lambda e: e.get("id", 0), reverse=True)
        elif sort_by == "random":
            import random
            shuffled = emojis.copy()
            random.shuffle(shuffled)
            return shuffled
        else:
            return emojis
    
    def get_trending_emojis(
        self,
        emojis: List[Dict[str, Any]],
        limit: int = 10,
        category: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get trending (most favorited) emojis.
        
        Args:
            emojis: List of emoji dictionaries
            limit: Maximum number of emojis to return
            category: Optional category filter
            
        Returns:
            List of trending emojis
        """
        filtered = self.filter_emojis(emojis, category=category, adult_filter=True)
        sorted_emojis = self.sort_emojis(filtered, sort_by="favorites")
        return sorted_emojis[:limit]
