# 💻 Implementation Examples

This document provides concrete code examples for implementing the external search and RAG functionality.

## 📦 1. FormulaKnowledgeBase Service

### File: `src/services/formula_kb.py`

```python
"""Formula Knowledge Base service for RAG operations."""

import json
import logging
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


@dataclass
class FormulaData:
    """Data class for formula information."""
    id: str
    formula: str
    normalized: str
    variants: List[str]
    name: str
    category: str
    description: str
    variables: Dict[str, str]
    applications: List[str]
    example: str


class FormulaKnowledgeBase:
    """Service for managing local formula knowledge base."""
    
    def __init__(self, kb_path: Path, similarity_threshold: float = 0.8):
        """
        Initialize knowledge base.
        
        Args:
            kb_path: Path to formulas_kb.json
            similarity_threshold: Minimum similarity score for fuzzy matching
        """
        self.kb_path = kb_path
        self.similarity_threshold = similarity_threshold
        self.formulas: List[FormulaData] = []
        self._load_knowledge_base()
    
    def _load_knowledge_base(self):
        """Load formulas from JSON file."""
        try:
            if not self.kb_path.exists():
                logger.warning(f"Knowledge base not found at {self.kb_path}")
                return
            
            with open(self.kb_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for formula_dict in data.get('formulas', []):
                formula = FormulaData(**formula_dict)
                self.formulas.append(formula)
            
            logger.info(f"Loaded {len(self.formulas)} formulas from knowledge base")
            
        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}")
    
    @staticmethod
    def normalize_formula(formula: str) -> str:
        """
        Normalize formula for comparison.
        
        Args:
            formula: Raw formula text
            
        Returns:
            Normalized formula (lowercase, no spaces, standardized)
        """
        # Remove spaces
        normalized = formula.replace(' ', '')
        
        # Convert to lowercase
        normalized = normalized.lower()
        
        # Standardize common notations
        replacements = {
            '^': '**',
            '×': '*',
            '·': '*',
            '÷': '/',
            '²': '2',
            '³': '3',
            '√': 'sqrt',
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        return normalized
    
    def calculate_similarity(self, formula1: str, formula2: str) -> float:
        """
        Calculate similarity between two formulas.
        
        Args:
            formula1: First formula
            formula2: Second formula
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        return SequenceMatcher(None, formula1, formula2).ratio()
    
    async def search_formula(self, formula_text: str) -> Optional[FormulaData]:
        """
        Search for formula in knowledge base.
        
        Args:
            formula_text: Formula to search for
            
        Returns:
            FormulaData if found, None otherwise
        """
        normalized = self.normalize_formula(formula_text)
        logger.info(f"Searching for formula: {formula_text} (normalized: {normalized})")
        
        # 1. Try exact match
        for formula in self.formulas:
            if normalized == formula.normalized:
                logger.info(f"Exact match found: {formula.name}")
                return formula
        
        # 2. Try variant match
        for formula in self.formulas:
            for variant in formula.variants:
                if normalized == self.normalize_formula(variant):
                    logger.info(f"Variant match found: {formula.name}")
                    return formula
        
        # 3. Try fuzzy match
        best_match = None
        best_score = 0.0
        
        for formula in self.formulas:
            score = self.calculate_similarity(normalized, formula.normalized)
            if score > self.similarity_threshold and score > best_score:
                best_match = formula
                best_score = score
        
        if best_match:
            logger.info(f"Fuzzy match found: {best_match.name} (score: {best_score:.2f})")
            return best_match
        
        logger.info("No match found in knowledge base")
        return None
    
    async def add_formula(self, formula_data: Dict) -> bool:
        """
        Add new formula to knowledge base.
        
        Args:
            formula_data: Dictionary with formula information
            
        Returns:
            True if added successfully
        """
        try:
            formula = FormulaData(**formula_data)
            self.formulas.append(formula)
            
            # Save to file
            data = {
                'formulas': [
                    {
                        'id': f.id,
                        'formula': f.formula,
                        'normalized': f.normalized,
                        'variants': f.variants,
                        'name': f.name,
                        'category': f.category,
                        'description': f.description,
                        'variables': f.variables,
                        'applications': f.applications,
                        'example': f.example
                    }
                    for f in self.formulas
                ]
            }
            
            with open(self.kb_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Added formula: {formula.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add formula: {e}")
            return False
```

---

## 🔍 2. SearchService Implementation

### File: `src/services/search_service.py`

```python
"""Search service for DuckDuckGo integration."""

import logging
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from langchain_community.tools import DuckDuckGoSearchResults

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
            cache_ttl: Cache time-to-live in seconds
        """
        self.cache_repo = cache_repository
        self.max_results = max_results
        self.cache_ttl = cache_ttl
        self.search_tool = DuckDuckGoSearchResults(max_results=max_results)
    
    def build_search_query(self, formula_text: str, formula_name: Optional[str] = None) -> str:
        """
        Build optimal search query.
        
        Args:
            formula_text: The formula text
            formula_name: Optional formula name
            
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
            from src.services.formula_kb import FormulaKnowledgeBase
            normalized = FormulaKnowledgeBase.normalize_formula(formula_text)
            
            # 1. Check cache first
            cached = await self.cache_repo.get_cached_search(normalized)
            if cached:
                logger.info(f"Cache hit for formula: {formula_text}")
                return cached
            
            # 2. Build search query
            query = self.build_search_query(formula_text, formula_name)
            
            # 3. Perform search
            logger.info(f"Searching internet for: {query}")
            results = self.search_tool.run(query)
            
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
            logger.error(f"Search failed for {formula_text}: {e}")
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
            # Parse results (DuckDuckGo returns JSON-like string)
            import json
            
            # Try to parse as JSON
            try:
                results_list = json.loads(results)
            except:
                # If not JSON, return as is
                return results
            
            # Format each result
            formatted_parts = []
            for i, result in enumerate(results_list[:self.max_results], 1):
                title = result.get('title', 'No title')
                snippet = result.get('snippet', 'No description')
                link = result.get('link', '')
                
                formatted_parts.append(
                    f"{i}. **{title}**\n"
                    f"   {snippet}\n"
                    f"   🔗 {link}"
                )
            
            return "\n\n".join(formatted_parts)
            
        except Exception as e:
            logger.error(f"Failed to format results: {e}")
            return results
```

---

## 🔄 3. Enhanced GigaChatService

### File: `src/services/gigachat_service.py` (additions)

```python
# Add to existing GigaChatService class

async def recognize_formula_with_search(self, file_id: str) -> str:
    """
    Recognize and explain formula using multi-chain approach.
    
    This implements a 4-chain workflow:
    1. Extract formula from image
    2. Check local RAG knowledge base
    3. Search internet for additional context
    4. Generate comprehensive explanation
    
    Args:
        file_id: GigaChat file ID of uploaded image
        
    Returns:
        Comprehensive explanation with citations
    """
    try:
        # Chain 1: Extract formula from image
        logger.info("Chain 1: Extracting formula from image")
        formula_text = await self._extract_formula_from_image(file_id)
        
        # Chain 2: Check RAG knowledge base
        logger.info("Chain 2: Checking local knowledge base")
        rag_data = None
        if self.formula_kb:
            rag_data = await self.formula_kb.search_formula(formula_text)
        
        # Chain 3: Search internet
        logger.info("Chain 3: Searching internet")
        search_results = None
        if self.search_service:
            formula_name = rag_data.name if rag_data else None
            search_results = await self.search_service.search_formula(
                formula_text,
                formula_name
            )
        
        # Chain 4: Generate comprehensive explanation
        logger.info("Chain 4: Generating comprehensive explanation")
        explanation = await self._explain_formula_with_context(
            formula_text=formula_text,
            rag_data=rag_data,
            search_results=search_results
        )
        
        return explanation
        
    except Exception as e:
        logger.error(f"Failed to recognize formula with search: {e}")
        raise


async def _explain_formula_with_context(
    self,
    formula_text: str,
    rag_data: Optional['FormulaData'],
    search_results: Optional[str]
) -> str:
    """
    Generate comprehensive explanation using all available context.
    
    Args:
        formula_text: Extracted formula
        rag_data: Data from RAG knowledge base (if found)
        search_results: Internet search results (if available)
        
    Returns:
        Comprehensive explanation with citations
    """
    # Build context sections
    rag_context = ""
    if rag_data:
        rag_context = f"""
**Информация из локальной базы знаний:**
- Название: {rag_data.name}
- Категория: {rag_data.category}
- Описание: {rag_data.description}
- Переменные: {', '.join(f'{k}: {v}' for k, v in rag_data.variables.items())}
"""
    
    search_context = ""
    if search_results:
        search_context = f"""
**Информация из интернета:**
{search_results}
"""
    
    # Build sources list
    sources = ["🤖 GigaChat AI"]
    if rag_data:
        sources.insert(0, "📚 Локальная база знаний")
    if search_results:
        sources.insert(1 if rag_data else 0, "🌐 Интернет-поиск (DuckDuckGo)")
    
    # Create enhanced prompt
    prompt_template = PromptTemplate(
        input_variables=["formula", "rag_context", "search_context", "sources"],
        template="""
Ты - опытный преподаватель математики и физики. Тебе дана формула:

{formula}

{rag_context}

{search_context}

Используя всю доступную информацию, предоставь подробное объяснение этой формулы:

1. **Название формулы**: Как называется эта формула?
2. **Область применения**: В какой области науки используется (математика, физика, химия и т.д.)?
3. **Что она описывает**: Какое явление или зависимость описывает эта формула?
4. **Объяснение переменных**: Расшифруй каждую переменную и символ в формуле
5. **Практическое применение**: Где и как эта формула применяется на практике?
6. **Пример использования**: Приведи простой пример расчета (если применимо)

**Источники информации:**
{sources}

Отвечай на русском языке, структурированно и понятно. Если информация из разных источников противоречит друг другу, укажи на это.
"""
    )
    
    # Generate explanation
    chain = prompt_template | self.llm
    response = chain.invoke({
        "formula": formula_text,
        "rag_context": rag_context,
        "search_context": search_context,
        "sources": "\n".join(f"- {s}" for s in sources)
    })
    
    return response.content
```

---

## 🗄️ 4. Database Models Update

### File: `src/database/models.py` (additions)

```python
# Add to existing models

CREATE_SEARCH_CACHE_TABLE = """
CREATE TABLE IF NOT EXISTS search_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    formula_normalized TEXT NOT NULL UNIQUE,
    search_query TEXT NOT NULL,
    results TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_formula_normalized ON search_cache(formula_normalized);
CREATE INDEX IF NOT EXISTS idx_expires_at ON search_cache(expires_at);
"""
```

### File: `src/database/repository.py` (additions)

```python
# Add to existing UserRepository class or create new CacheRepository

async def get_cached_search(self, formula_normalized: str) -> Optional[str]:
    """
    Get cached search results for formula.
    
    Args:
        formula_normalized: Normalized formula text
        
    Returns:
        Cached results or None if not found/expired
    """
    async with aiosqlite.connect(self.db_path) as db:
        async with db.execute(
            """
            SELECT results FROM search_cache
            WHERE formula_normalized = ?
            AND expires_at > datetime('now')
            """,
            (formula_normalized,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def cache_search_results(
    self,
    formula_normalized: str,
    search_query: str,
    results: str,
    ttl_seconds: int
) -> bool:
    """
    Cache search results.
    
    Args:
        formula_normalized: Normalized formula text
        search_query: The search query used
        results: Search results to cache
        ttl_seconds: Time to live in seconds
        
    Returns:
        True if cached successfully
    """
    try:
        from datetime import datetime, timedelta
        
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO search_cache
                (formula_normalized, search_query, results, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (formula_normalized, search_query, results, expires_at.isoformat())
            )
            await db.commit()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to cache search results: {e}")
        return False


async def cleanup_expired_cache(self):
    """Remove expired cache entries."""
    async with aiosqlite.connect(self.db_path) as db:
        await db.execute(
            "DELETE FROM search_cache WHERE expires_at < datetime('now')"
        )
        await db.commit()
```

---

## 📝 5. Initial Knowledge Base

### File: `data/formulas_kb.json`

```json
{
  "formulas": [
    {
      "id": "einstein_mass_energy",
      "formula": "E = mc²",
      "normalized": "e=mc2",
      "variants": ["E=mc^2", "E = m*c^2", "E = m * c²"],
      "name": "Формула Эйнштейна (масса-энергия)",
      "category": "physics",
      "description": "Устанавливает эквивалентность массы и энергии",
      "variables": {
        "E": "Энергия (Джоули)",
        "m": "Масса (килограммы)",
        "c": "Скорость света (≈3×10⁸ м/с)"
      },
      "applications": [
        "Ядерная физика",
        "Релятивистская механика",
        "Астрофизика"
      ],
      "example": "Для массы 1 кг: E = 1 × (3×10⁸)² = 9×10¹⁶ Дж"
    },
    {
      "id": "newton_second_law",
      "formula": "F = ma",
      "normalized": "f=ma",
      "variants": ["F=m*a", "F = m * a"],
      "name": "Второй закон Ньютона",
      "category": "physics",
      "description": "Связывает силу, массу и ускорение",
      "variables": {
        "F": "Сила (Ньютоны)",
        "m": "Масса (килограммы)",
        "a": "Ускорение (м/с²)"
      },
      "applications": [
        "Классическая механика",
        "Динамика",
        "Инженерия"
      ],
      "example": "Для массы 10 кг и ускорения 2 м/с²: F = 10 × 2 = 20 Н"
    },
    {
      "id": "pythagorean_theorem",
      "formula": "a² + b² = c²",
      "normalized": "a2+b2=c2",
      "variants": ["a^2 + b^2 = c^2", "a**2 + b**2 = c**2"],
      "name": "Теорема Пифагора",
      "category": "mathematics",
      "description": "Соотношение между сторонами прямоугольного треугольника",
      "variables": {
        "a": "Катет (длина)",
        "b": "Катет (длина)",
        "c": "Гипотенуза (длина)"
      },
      "applications": [
        "Геометрия",
        "Тригонометрия",
        "Строительство"
      ],
      "example": "Для катетов 3 и 4: c² = 9 + 16 = 25, c = 5"
    }
  ]
}
```

---

## ⚙️ 6. Configuration Updates

### File: `src/config/settings.py` (additions)

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Search Configuration
    enable_search: bool = True
    search_max_results: int = 5
    search_cache_ttl: int = 86400  # 24 hours
    always_search: bool = False  # Search even if found in RAG
    
    # RAG Configuration
    enable_rag: bool = True
    formulas_kb_path: str = "data/formulas_kb.json"
    rag_similarity_threshold: float = 0.8
    
    @property
    def kb_path(self) -> Path:
        """Get knowledge base path as Path object."""
        return Path(self.formulas_kb_path)
```

---

## 🚀 7. Main Application Updates

### File: `src/main.py` (additions)

```python
async def main():
    # ... existing code ...
    
    # Initialize services
    user_repo = UserRepository(settings.db_path)
    
    # Initialize Formula KB
    formula_kb = None
    if settings.enable_rag:
        formula_kb = FormulaKnowledgeBase(
            kb_path=settings.kb_path,
            similarity_threshold=settings.rag_similarity_threshold
        )
    
    # Initialize Search Service
    search_service = None
    if settings.enable_search:
        search_service = SearchService(
            cache_repository=user_repo,
            max_results=settings.search_max_results,
            cache_ttl=settings.search_cache_ttl
        )
    
    # Initialize GigaChat with new services
    gigachat_service = GigaChatService(
        credentials=settings.gigachat_key,
        scope=settings.gigachat_scope,
        model=settings.gigachat_model,
        formula_kb=formula_kb,
        search_service=search_service
    )
    
    # ... rest of the code ...
```

---

## 🧪 8. Testing Examples

### Test Script: `tests/test_chains.py`

```python
"""Test multi-chain workflow."""

import asyncio
from pathlib import Path
from src.services.formula_kb import FormulaKnowledgeBase
from src.services.search_service import SearchService


async def test_rag_lookup():
    """Test RAG knowledge base lookup."""
    kb = FormulaKnowledgeBase(
        kb_path=Path("data/formulas_kb.json"),
        similarity_threshold=0.8
    )
    
    # Test exact match
    result = await kb.search_formula("E = mc²")
    assert result is not None
    assert result.name == "Формула Эйнштейна (масса-энергия)"
    
    # Test variant match
    result = await kb.search_formula("E=mc^2")
    assert result is not None
    
    # Test fuzzy match
    result = await kb.search_formula("E = m*c*c")
    assert result is not None
    
    print("✅ RAG tests passed")


async def test_search():
    """Test internet search."""
    # Mock cache repository
    class MockRepo:
        async def get_cached_search(self, formula):
            return None
        async def cache_search_results(self, *args):
            return True
    
    search = SearchService(
        cache_repository=MockRepo(),
        max_results=3
    )
    
    results = await search.search_formula("E = mc²", "Einstein formula")
    assert results is not None
    print(f"Search results:\n{results}")
    print("✅ Search tests passed")


if __name__ == "__main__":
    asyncio.run(test_rag_lookup())
    asyncio.run(test_search())
```

---

**These examples provide a complete implementation guide for the multi-chain workflow with RAG and external search!** 🚀