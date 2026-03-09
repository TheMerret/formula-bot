"""Web-based RAG service for mathematical formulas."""

import logging
import string
from typing import Optional

from langchain.prompts import PromptTemplate
from langchain.retrievers import BM25Retriever
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class FormulaRAGService:
    """Web-based RAG service for mathematical formulas using BM25 retrieval."""
    
    def __init__(
        self,
        llm,
        source_urls: list[str],
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        k: int = 3
    ):
        """
        Initialize FormulaRAGService.
        
        Args:
            llm: LangChain LLM instance (GigaChat) for query rewriting
            source_urls: List of URLs to load LaTeX formulas from
            chunk_size: Size of text chunks for splitting
            chunk_overlap: Overlap between chunks
            k: Number of chunks to retrieve per query
        """
        self.llm = llm
        self.source_urls = source_urls
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.k = k
        self.retriever = None
        self.is_initialized = False
        
        logger.info(
            f"FormulaRAGService created with {len(source_urls)} sources, "
            f"chunk_size={chunk_size}, k={k}"
        )
    
    async def initialize(self) -> None:
        """
        Load documents from web and initialize BM25 retriever.
        
        This method:
        1. Loads LaTeX documents from configured URLs
        2. Splits documents into chunks
        3. Creates BM25 retriever for fast formula matching
        
        Raises:
            Exception: If initialization fails
        """
        try:
            logger.info(f"Loading LaTeX formulas from {len(self.source_urls)} sources...")
            
            # Load documents from URLs
            loader = WebBaseLoader(self.source_urls)
            docs = loader.load()
            
            logger.info(f"Loaded {len(docs)} documents")
            
            if not docs:
                logger.warning("No documents loaded from sources")
                self.is_initialized = False
                return
            
            # Split documents into chunks with LaTeX-specific separators
            text_splitter = RecursiveCharacterTextSplitter(
                separators=["\n\n", "\n", "\\\\", "$$", "$"],  # LaTeX separators
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
            )
            
            split_docs = text_splitter.split_documents(docs)
            logger.info(f"Split into {len(split_docs)} chunks")
            
            if not split_docs:
                logger.warning("No chunks created from documents")
                self.is_initialized = False
                return
            
            # Create BM25 retriever
            self.retriever = BM25Retriever.from_documents(
                documents=split_docs,
                preprocess_func=self._tokenize,
                k=self.k
            )
            
            self.is_initialized = True
            logger.info("FormulaRAGService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}", exc_info=True)
            self.is_initialized = False
            raise
    
    def search_formula(self, formula_text: str) -> Optional[str]:
        """
        Search for formula in RAG knowledge base.
        
        Uses query rewriting + BM25 retrieval for better results:
        1. Rewrites query into 3 variants using LLM
        2. Retrieves relevant chunks for each variant
        3. Deduplicates and aggregates results
        4. Returns formatted context
        
        Args:
            formula_text: Extracted formula text
            
        Returns:
            Formatted context from retrieved chunks or None if not found
        """
        if not self.is_initialized or not self.retriever:
            logger.warning("RAG service not initialized, skipping search")
            return None
        
        try:
            logger.info(f"Searching RAG for formula: {formula_text}")
            
            # 1. Rewrite query into variants
            query_variants = self._rewrite_query(formula_text)
            logger.info(f"Generated {len(query_variants)} query variants")
            
            # 2. Retrieve for each variant
            all_chunks = []
            seen = set()
            
            for i, variant in enumerate(query_variants, 1):
                logger.debug(f"Retrieving for variant {i}: {variant}")
                
                try:
                    results = self.retriever.get_relevant_documents(variant)
                    
                    for doc in results:
                        # Deduplicate by first 100 chars
                        content_key = doc.page_content[:100]
                        if content_key not in seen:
                            seen.add(content_key)
                            all_chunks.append(doc.page_content)
                            
                except Exception as e:
                    logger.warning(f"Retrieval failed for variant '{variant}': {e}")
                    continue
            
            if not all_chunks:
                logger.info("No relevant formulas found in RAG")
                return None
            
            # 3. Format context
            context = self._format_context(all_chunks)
            logger.info(f"Retrieved {len(all_chunks)} relevant chunks from RAG")
            
            return context
            
        except Exception as e:
            logger.error(f"RAG search failed: {e}", exc_info=True)
            return None
    
    def _rewrite_query(self, query: str) -> list[str]:
        """
        Generate query variants using LLM for better retrieval.
        
        Creates 3 variants of the formula query using different notations
        and formats to improve retrieval success rate.
        
        Args:
            query: Original formula query
            
        Returns:
            List of query variants (including original)
        """
        prompt_template = PromptTemplate(
            input_variables=["query"],
            template="""Перефразируй математическую формулу 3 раза, сохраняя смысл.
Используй разные обозначения и форматы (LaTeX, текстовый, символьный).
Верни каждый вариант с новой строки без нумерации.

Формула: {query}

Варианты:"""
        )
        
        try:
            chain = prompt_template | self.llm
            response = chain.invoke({"query": query})
            
            # Parse response
            rewrites = response.content.strip().split('\n')
            rewrites = [r.strip() for r in rewrites if r.strip()]
            
            # Limit to 3 variants
            rewrites = rewrites[:3]
            
            # Always include original query if not present
            if query not in rewrites:
                rewrites.insert(0, query)
            
            # Ensure we have at least the original
            if not rewrites:
                rewrites = [query]
            
            logger.debug(f"Query variants: {rewrites}")
            return rewrites[:3]
            
        except Exception as e:
            logger.error(f"Query rewriting failed: {e}")
            # Fallback to original query
            return [query]
    
    def _tokenize(self, text: str) -> list[str]:
        """
        Tokenize text for BM25 retrieval.
        
        Converts text to lowercase and removes punctuation for better matching.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of tokens
        """
        # Lowercase and remove punctuation
        cleaned = text.lower().translate(
            str.maketrans("", "", string.punctuation)
        )
        
        # Split into tokens
        tokens = cleaned.split()
        
        return tokens
    
    def _format_context(self, chunks: list[str]) -> str:
        """
        Format retrieved chunks into context string.
        
        Args:
            chunks: List of retrieved text chunks
            
        Returns:
            Formatted context string
        """
        if not chunks:
            return ""
        
        # Limit to top chunks to avoid token overflow
        max_chunks = 5
        selected_chunks = chunks[:max_chunks]
        
        formatted = "**Информация из базы знаний (HSE Mathematical Analysis):**\n\n"
        
        for i, chunk in enumerate(selected_chunks, 1):
            # Clean LaTeX formatting for better readability
            cleaned = chunk.replace('\\\\', '\n').replace('$$', '')
            
            # Truncate very long chunks
            if len(cleaned) > 500:
                cleaned = cleaned[:500] + "..."
            
            formatted += f"{i}. {cleaned}\n\n"
        
        return formatted.strip()