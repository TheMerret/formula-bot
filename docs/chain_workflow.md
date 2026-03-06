# 🔄 Multi-Chain Workflow Diagram

## Complete Processing Flow

```mermaid
graph TB
    Start([User sends formula image]) --> Upload[Upload to Telegram]
    Upload --> Chain1[Chain 1: Extract Formula]
    
    Chain1 --> |Formula Text| Chain2{Chain 2: RAG Lookup}
    
    Chain2 --> |Found| RAGHit[Use RAG Data]
    Chain2 --> |Not Found| Chain3[Chain 3: Internet Search]
    
    Chain3 --> |Search Results| Combine[Combine Context]
    RAGHit --> Combine
    
    Combine --> Chain4[Chain 4: Generate Explanation]
    Chain4 --> Format[Format Response with Citations]
    Format --> Send([Send to User])
    
    style Chain1 fill:#e1f5ff
    style Chain2 fill:#fff4e1
    style Chain3 fill:#ffe1f5
    style Chain4 fill:#e1ffe1
    style RAGHit fill:#d4edda
    style Combine fill:#fff3cd
```

## Detailed Chain Breakdown

### Chain 1: Formula Extraction
```mermaid
graph LR
    A[Image File ID] --> B[GigaChat Vision API]
    B --> C[Extract Text/LaTeX]
    C --> D[Normalize Formula]
    D --> E[Formula Text]
    
    style B fill:#4a90e2
    style E fill:#7ed321
```

**Time**: ~10-15 seconds  
**Technology**: GigaChat Vision Model  
**Output**: Normalized formula text

---

### Chain 2: RAG Knowledge Base
```mermaid
graph LR
    A[Formula Text] --> B[Load KB from JSON]
    B --> C{Exact Match?}
    C --> |Yes| D[Return RAG Data]
    C --> |No| E{Variant Match?}
    E --> |Yes| D
    E --> |No| F{Fuzzy Match > 0.8?}
    F --> |Yes| D
    F --> |No| G[Return None]
    
    style D fill:#7ed321
    style G fill:#f5a623
```

**Time**: <1 second (in-memory)  
**Technology**: Custom Python service + JSON  
**Output**: Formula metadata or None

---

### Chain 3: Internet Search
```mermaid
graph LR
    A[Formula + Name] --> B{Check Cache?}
    B --> |Hit| C[Return Cached]
    B --> |Miss| D[Build Query]
    D --> E[DuckDuckGo Search]
    E --> F[Extract Snippets]
    F --> G[Cache Results]
    G --> H[Return Results]
    
    style C fill:#7ed321
    style E fill:#4a90e2
    style G fill:#f8e71c
```

**Time**: 2-3 seconds (or <1s if cached)  
**Technology**: DuckDuckGo API + SQLite cache  
**Output**: Search results with URLs

---

### Chain 4: Comprehensive Explanation
```mermaid
graph TB
    A[Formula Text] --> D[Build Enhanced Prompt]
    B[RAG Data] --> D
    C[Search Results] --> D
    D --> E[GigaChat LLM]
    E --> F[Generate Explanation]
    F --> G[Add Citations]
    G --> H[Format Response]
    
    style E fill:#4a90e2
    style H fill:#7ed321
```

**Time**: ~10-15 seconds  
**Technology**: GigaChat + LangChain  
**Output**: Comprehensive explanation with sources

---

## Data Flow Example

### Example: E = mc²

```mermaid
sequenceDiagram
    participant U as User
    participant B as Bot
    participant C1 as Chain 1<br/>(Vision)
    participant C2 as Chain 2<br/>(RAG)
    participant C3 as Chain 3<br/>(Search)
    participant C4 as Chain 4<br/>(LLM)
    
    U->>B: Sends image of E=mc²
    B->>C1: Upload image
    C1->>C1: Extract formula
    C1-->>B: "E = mc²"
    
    B->>C2: Search in RAG
    C2->>C2: Check formulas_kb.json
    C2-->>B: Found! (Einstein formula data)
    
    B->>C3: Search internet (optional)
    C3->>C3: Check cache
    C3->>C3: DuckDuckGo search
    C3-->>B: Wikipedia + articles
    
    B->>C4: Generate explanation
    C4->>C4: Combine all context
    C4->>C4: Generate with GigaChat
    C4-->>B: Comprehensive explanation
    
    B->>U: Send formatted response<br/>with citations
```

---

## Performance Optimization

### Parallel Processing
```mermaid
graph TB
    Start[Formula Extracted] --> Decision{RAG Enabled?}
    Decision --> |Yes| Parallel[Run in Parallel]
    Decision --> |No| Search[Only Search]
    
    Parallel --> RAG[RAG Lookup]
    Parallel --> SearchP[Internet Search]
    
    RAG --> Wait[Wait for Both]
    SearchP --> Wait
    
    Wait --> Combine[Combine Results]
    Search --> Combine
    
    Combine --> Generate[Generate Explanation]
    
    style Parallel fill:#7ed321
    style Wait fill:#f8e71c
```

**Optimization**: Run RAG and Search concurrently using `asyncio.gather()`

---

## Error Handling Flow

```mermaid
graph TB
    Start[Start Processing] --> C1[Chain 1: Extract]
    C1 --> |Success| C2[Chain 2: RAG]
    C1 --> |Fail| Error1[Return Error]
    
    C2 --> |Success| C3[Chain 3: Search]
    C2 --> |Fail| C3
    
    C3 --> |Success| C4[Chain 4: Explain]
    C3 --> |Fail| C4
    
    C4 --> |Success| Success[Send Response]
    C4 --> |Fail| Fallback[Basic Explanation]
    
    Fallback --> Success
    
    style Success fill:#7ed321
    style Error1 fill:#d0021b
    style Fallback fill:#f5a623
```

**Principle**: Always provide a response, even if some chains fail

---

## Cache Strategy

```mermaid
graph LR
    A[Request] --> B{RAG Cache<br/>In Memory?}
    B --> |Hit| C[Return Immediately]
    B --> |Miss| D{Search Cache<br/>SQLite?}
    D --> |Hit & Fresh| E[Return from DB]
    D --> |Miss/Expired| F[Fetch from Internet]
    F --> G[Store in Cache]
    G --> H[Return Results]
    
    style C fill:#7ed321
    style E fill:#7ed321
    style G fill:#f8e71c
```

**Cache Layers**:
1. **RAG**: In-memory (permanent)
2. **Search**: SQLite (24h TTL)

---

## Response Format Structure

```mermaid
graph TB
    A[Raw Data] --> B[Format Header]
    B --> C[Add Formula Name]
    C --> D[Add Description]
    D --> E[Add Variables]
    E --> F[Add Applications]
    F --> G[Add Example]
    G --> H[Add Sources]
    H --> I[Add Web Links]
    I --> J[Final Response]
    
    style J fill:#7ed321
```

---

## System Architecture

```mermaid
graph TB
    subgraph "Telegram Bot Layer"
        TG[Telegram API]
        Handler[Formula Handler]
    end
    
    subgraph "Service Layer"
        GC[GigaChat Service]
        RAG[Formula KB Service]
        Search[Search Service]
    end
    
    subgraph "Data Layer"
        JSON[formulas_kb.json]
        Cache[SQLite Cache]
        UserDB[Users DB]
    end
    
    subgraph "External APIs"
        GigaAPI[GigaChat API]
        DDG[DuckDuckGo]
    end
    
    TG --> Handler
    Handler --> GC
    GC --> RAG
    GC --> Search
    GC --> GigaAPI
    
    RAG --> JSON
    Search --> Cache
    Search --> DDG
    Handler --> UserDB
    
    style GC fill:#4a90e2
    style RAG fill:#7ed321
    style Search fill:#f5a623
```

---

## Deployment Flow

```mermaid
graph LR
    A[Code Changes] --> B[Update Dependencies]
    B --> C[Create Data Files]
    C --> D[Run Migrations]
    D --> E[Test Locally]
    E --> F{Tests Pass?}
    F --> |Yes| G[Build Docker]
    F --> |No| A
    G --> H[Deploy]
    H --> I[Monitor Logs]
    
    style G fill:#7ed321
    style I fill:#f8e71c
```

---

**Note**: All diagrams use Mermaid syntax and can be rendered in GitHub, VS Code, or any Mermaid-compatible viewer.