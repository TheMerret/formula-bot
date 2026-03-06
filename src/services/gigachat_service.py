"""GigaChat API service for formula recognition."""

import logging
from typing import BinaryIO, Optional

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from langchain.prompts import PromptTemplate
from langchain_gigachat.chat_models import GigaChat as LangChainGigaChat
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)


class GigaChatService:
    """Service for interacting with GigaChat API."""
    
    def __init__(
        self,
        credentials: str,
        scope: str = "GIGACHAT_API_PERS",
        model: str = "GigaChat-Pro",
        search_service: Optional['SearchService'] = None
    ):
        """
        Initialize GigaChat service.
        
        Args:
            credentials: GigaChat API credentials
            scope: API scope
            model: Model name to use
            search_service: Optional SearchService for internet search integration
        """
        self.credentials = credentials
        self.scope = scope
        self.model = model
        self.search_service = search_service
        
        # Initialize GigaChat client for image upload
        self.client = GigaChat(
            credentials=credentials,
            verify_ssl_certs=False,
            scope=scope
        )
        
        # Initialize LangChain GigaChat for advanced prompting
        self.llm = LangChainGigaChat(
            credentials=credentials,
            scope=scope,
            model=model,
            temperature=0.1,
            verify_ssl_certs=False
        )
        
        logger.info(f"GigaChat service initialized with model: {model}")
    
    async def upload_image(self, image_file: BinaryIO) -> str:
        """
        Upload an image to GigaChat and get file ID.
        
        Args:
            image_file: Binary file object of the image
            
        Returns:
            File ID for the uploaded image
            
        Raises:
            Exception: If upload fails
        """
        try:
            uploaded_file = self.client.upload_file(image_file)
            file_id = uploaded_file.id_
            logger.info(f"Image uploaded successfully, file_id: {file_id}")
            return file_id
        except Exception as e:
            logger.error(f"Failed to upload image: {e}")
            raise
    
    async def recognize_formula(self, file_id: str) -> str:
        """
        Recognize and explain a mathematical formula from an image.
        
        This implements a two-chain approach:
        Chain 1: Image → Formula extraction
        Chain 2: Formula → Detailed explanation
        
        Args:
            file_id: GigaChat file ID of the uploaded image
            
        Returns:
            Detailed explanation of the formula
            
        Raises:
            Exception: If recognition fails
        """
        try:
            # Chain 1: Extract formula from image
            logger.info("Chain 1: Extracting formula from image")
            formula_text = await self._extract_formula_from_image(file_id)
            
    
    async def recognize_formula_with_search(self, file_id: str) -> str:
        """
        Recognize and explain a mathematical formula with internet search enhancement.
        
        This implements a three-chain approach:
        Chain 1: Image → Formula extraction
        Chain 2: Formula → Internet search for context
        Chain 3: Formula + Search context → Detailed explanation
        
        Args:
            file_id: GigaChat file ID of the uploaded image
            
        Returns:
            Detailed explanation of the formula with search context
            
        Raises:
            Exception: If recognition fails
        """
        try:
            # Chain 1: Extract formula from image
            logger.info("Chain 1: Extracting formula from image")
            formula_text = await self._extract_formula_from_image(file_id)
            
            # Chain 2: Search internet for context (if search service available)
            search_results = None
            if self.search_service:
                logger.info("Chain 2: Searching internet for formula context")
                search_results = await self.search_service.search_formula(formula_text)
            else:
                logger.info("Chain 2: Skipped (search service not available)")
            
            # Chain 3: Get detailed explanation with search context
            logger.info("Chain 3: Generating comprehensive explanation")
            explanation = await self._explain_formula_with_context(formula_text, search_results)
            
            return explanation
            
        except Exception as e:
            logger.error(f"Failed to recognize formula with search: {e}")
            raise
            # Chain 2: Get detailed explanation
            logger.info("Chain 2: Getting formula explanation")
            explanation = await self._explain_formula(formula_text)
            
            return explanation
            
        except Exception as e:
            logger.error(f"Failed to recognize formula: {e}")
            raise
    
    async def _extract_formula_from_image(self, file_id: str) -> str:
        """
        Chain 1: Extract formula text from image.
        
        Args:
            file_id: GigaChat file ID
            
        Returns:
            Extracted formula text
        """
        prompt = """
Проанализируй изображение и извлеки математическую формулу.

Твоя задача:
1. Распознать все математические символы, переменные и операторы
2. Записать формулу в текстовом виде (используй LaTeX нотацию если возможно)
3. Если формула написана от руки, постарайся точно распознать все символы

Верни только саму формулу без дополнительных объяснений.
"""
        
        human_message = [HumanMessage(
            content=prompt,
            additional_kwargs={"attachments": [file_id]}
        )]
        
        response = self.llm.invoke(human_message)
        formula_text = response.content.strip()
        
        logger.info(f"Extracted formula: {formula_text}")
        return formula_text
    
    async def _explain_formula(self, formula_text: str) -> str:
        """
        Chain 2: Get detailed explanation of the formula.
        
        Args:
            formula_text: The extracted formula text
            
        Returns:
            Detailed explanation
        """
        prompt_template = PromptTemplate(
            input_variables=["formula"],
            template="""
Ты - опытный преподаватель математики и физики. Тебе дана формула:

{formula}

Предоставь подробное объяснение этой формулы:

1. **Название формулы**: Как называется эта формула?
2. **Область применения**: В какой области науки используется (математика, физика, химия и т.д.)?
3. **Что она описывает**: Какое явление или зависимость описывает эта формула?
4. **Объяснение переменных**: Расшифруй каждую переменную и символ в формуле
5. **Практическое применение**: Где и как эта формула применяется на практике?
6. **Пример использования**: Приведи простой пример расчета (если применимо)

    
    async def _explain_formula_with_context(
        self,
        formula_text: str,
        search_results: Optional[str]
    ) -> str:
        """
        Chain 3: Get detailed explanation with search context.
        
        Args:
            formula_text: The extracted formula text
            search_results: Internet search results (if available)
            
        Returns:
            Detailed explanation with search context
        """
        # Build context section
        search_context = ""
        sources = ["🤖 GigaChat AI"]
        
        if search_results:
            search_context = f"""

**Дополнительная информация из интернета:**
{search_results}
"""
            sources.insert(0, "🌐 Интернет-поиск (DuckDuckGo)")
        
        prompt_template = PromptTemplate(
            input_variables=["formula", "search_context", "sources"],
            template="""
Ты - опытный преподаватель математики и физики. Тебе дана формула:

{formula}
{search_context}

Используя всю доступную информацию, предоставь подробное объяснение этой формулы:

1. **Название формулы**: Как называется эта формула?
2. **Область применения**: В какой области науки используется (математика, физика, химия и т.д.)?
3. **Что она описывает**: Какое явление или зависимость описывает эта формула?
4. **Объяснение переменных**: Расшифруй каждую переменную и символ в формуле
5. **Практическое применение**: Где и как эта формула применяется на практике?
6. **Пример использования**: Приведи простой пример расчета (если применимо)

---

**Источники информации:**
{sources}

Отвечай на русском языке, структурированно и понятно.
"""
        )
        
        chain = prompt_template | self.llm
        response = chain.invoke({
            "formula": formula_text,
            "search_context": search_context,
            "sources": "\n".join(f"- {s}" for s in sources)
        })
        explanation = response.content
        
        logger.info("Formula explanation with context generated successfully")
        return explanation
Отвечай на русском языке, структурированно и понятно.
"""
        )
        
        chain = prompt_template | self.llm
        response = chain.invoke({"formula": formula_text})
        explanation = response.content
        
        logger.info("Formula explanation generated successfully")
        return explanation
    
    async def simple_chat(self, user_message: str, system_prompt: str = None) -> str:
        """
        Simple chat interaction with GigaChat.
        
        Args:
            user_message: User's message
            system_prompt: Optional system prompt
            
        Returns:
            Assistant's response
        """
        messages = []
        
        if system_prompt:
            messages.append(Messages(role=MessagesRole.SYSTEM, content=system_prompt))
        
        messages.append(Messages(role=MessagesRole.USER, content=user_message))
        
        payload = Chat(
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        response = self.client.chat(payload)
        return response.choices[0].message.content