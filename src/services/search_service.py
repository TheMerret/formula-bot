"""Search service for DuckDuckGo integration."""

import logging
import asyncio
from typing import Optional
from datetime import datetime, timedelta
from langchain_community.tools import DuckDuckGoSearchResults
from duckduckgo_search.exceptions import RatelimitException

logger = logging.getLogger(__name__)


class SearchService:
    """Service for internet search with caching."""
    
    def __init__(
        self,
        cache_repository,
        max_results: int = 5,
        cache_ttl: int = 86400
    ):
        """
        Initialize search service.
        
        Args:
            cache_repository: Repository for cache operations
            max_results: Maximum search results to return
            cache_ttl: Cache time-to-live in seconds (default: 24 hours)
        """
        self.cache_repo = cache_repository
        self.max_results = max_results
        self.cache_ttl = cache_ttl
        self.search_tool = DuckDuckGoSearchResults(max_results=max_results)
        logger.info(f"SearchService initialized with max_results={max_results}, cache_ttl={cache_ttl}s")
    
    @staticmethod
    def normalize_formula(formula: str) -> str:
        """
        Normalize formula for cache key.
        
        Args:
            formula: Raw formula text
            
        Returns:
            Normalized formula (lowercase, no spaces)
        """
        # Remove spaces and convert to lowercase
        normalized = formula.replace(' ', '').lower()
        
        # Standardize common notations
        replacements = {
            '^': '**',
            '×': '*',
            '·': '*',
            '÷': '/',
            '²': '2',
            '³': '3',
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        return normalized
    
    def build_search_query(self, formula_text: str, formula_name: Optional[str] = None) -> str:
        """
        Build optimal search query.
        
        Args:
            formula_text: The formula text
            formula_name: Optional formula name for better results
            
        Returns:
            Search query string
        """
        if formula_name:
            # Use formula name for better results
            query = f"{formula_name} formula explanation"
        else:
            # Use formula text
            query = f"{formula_text} formula what is"
        
        logger.info(f"Built search query: {query}")
        return query
    
    async def search_formula(
        self,
        formula_text: str,
        formula_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Search for formula information on the internet.
        
        Args:
            formula_text: Formula to search for
            formula_name: Optional formula name for better results
            
        Returns:
            Search results as formatted string or None
        """
        try:
            # Normalize formula for cache key
            normalized = self.normalize_formula(formula_text)
            
            # 1. Check cache first
            cached = await self.cache_repo.get_cached_search(normalized)
            if cached:
                logger.info(f"Cache hit for formula: {formula_text}")
                return cached
            
            # 2. Build search query
            query = self.build_search_query(formula_text, formula_name)
            
            # 3. Perform search with retry logic
            logger.info(f"Searching internet for: {query}")
            results = await self._search_with_retry(query)
            
            if results is None:
                logger.warning(f"Search failed after retries for: {formula_text}")
                return None
            
            # 4. Format results
            formatted = self._format_search_results(results)
            
            # 5. Cache results
            await self.cache_repo.cache_search_results(
                normalized,
                query,
                formatted,
                self.cache_ttl
            )
            
            logger.info(f"Search completed and cached for: {formula_text}")
            return formatted
            
        except Exception as e:
            logger.error(f"Search failed for {formula_text}: {e}", exc_info=True)
            return None
    
    async def _search_with_retry(
        self,
        query: str,
        max_retries: int = 3,
        initial_delay: float = 2.0
    ) -> Optional[str]:
        """
        Perform search with exponential backoff retry logic.
        
        Args:
            query: Search query
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds before first retry
            
        Returns:
            Search results or None if all retries failed
        """
        delay = initial_delay
        
        for attempt in range(max_retries):
            try:
                # Run search in executor to avoid blocking
                loop = asyncio.get_event_loop()
                results = await loop.run_in_executor(
                    None,
                    self.search_tool.run,
                    query
                )
                return results
                
            except RatelimitException as e:
                logger.warning(
                    f"Rate limit hit on attempt {attempt + 1}/{max_retries}: {e}"
                )
                
                if attempt < max_retries - 1:
                    logger.info(f"Waiting {delay:.1f}s before retry...")
                    await asyncio.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    logger.error(
                        f"Search failed after {max_retries} attempts due to rate limiting"
                    )
                    return None
                    
            except Exception as e:
                logger.error(f"Search error on attempt {attempt + 1}: {e}", exc_info=True)
                
                if attempt < max_retries - 1:
                    logger.info(f"Waiting {delay:.1f}s before retry...")
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    return None
        
        return None
    
    def _format_search_results(self, results: str) -> str:
        """
        Format search results for display.
        
        Args:
            results: Raw search results
            
        Returns:
            Formatted results string
        """
        try:
            # DuckDuckGo returns a string representation of results
            # Try to parse and format nicely
            if not results or results == "[]":
                return "Результаты поиска не найдены."
            
            # Clean up the results string
            formatted = results.replace("', '", "'\n'")
            formatted = formatted.replace("[{", "[\n{")
            formatted = formatted.replace("}, {", "},\n{")
            
            return formatted
            
        except Exception as e:
            logger.error(f"Failed to format results: {e}")
            return results if results else "Ошибка форматирования результатов поиска."