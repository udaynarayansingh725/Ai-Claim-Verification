# 🔍 AI GENERATED CONTENT DETECTION ENGINE

AI GENERATED CONTENT DETECTION ENGINE is an open-source, highly concurrent AI fact-checking pipeline and fake-content detection backend system. 

## 🚀 What it is and What it does

This engine provides a robust backend to instantly analyze text, links, documents, and images to determine their factual accuracy and authenticity. 

### Key Features
- **Fact-Checking Pipeline (WebSocket):** Built for real-time streaming, the core pipeline can take a piece of content (or URL), scrape it, extract claims using LLMs, search the web concurrently for evidence, and evaluate each claim's truthfulness, streaming the progress back to the user instantly.
- **AI Content Detection (REST):** Dedicated endpoints to detect whether Texts, PDFs, or Images have been synthetically generated or altered by AI.
- **Async & Multi-threaded:** Uses `asyncio` and thread pools in Python to handle intensive blocking tasks (like web scraping and search) so that the application maintains high throughput.

## 🛠️ How it works

The backend is built with:
- **FastAPI** for high-performance REST and WebSocket routing.
- **Google Gemini API** for LLM-based claim extraction, fake-content detection, and verifying factualness.
- **Web Search Agents** (DuckDuckGo / Tavily) to pull real-time evidence safely.
- **PostgreSQL** paired with async SQLAlchemy / Alembic for safely storing fact-check reports asynchronously.

---

## ⚙️ Setup Guide

### 1. Prerequisites
- Python 3.10+
- PostgreSQL server running locally or externally.

### 2. Environment Variables (`.env`)
Create a `.env` file in the root directory and add the following required variables:

```env
# Google Gemini API key for claim extraction and AI detection
GEMINI_API_KEY=your_gemini_api_key_here

# Tavily API key for robust web search
TAVILY_API_KEY=your_tavily_api_key_here

# PostgreSQL database connection string (asyncpg format)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/factify

# Application settings
LOG_LEVEL=DEBUG
APP_ENV=development
```

### 3. Installation
Clone the repository and install the required dependencies:

```bash
# Clone the repository
git clone https://github.com/yourusername/factify.git
cd factify

# Create and activate a virtual environment
python -m venv venv

# On Windows
venv\Scripts\activate
# On Mac/Linux
source venv/bin/activate

# Install the Python dependencies
pip install -r requirements.txt
```

### 4. Database Setup (Docker)
The easiest way to run the required PostgreSQL database is via the included Docker Compose configuration. Ensure you have Docker installed and run:

```bash
docker-compose up -d db
```
This will start the postgres server automatically.

### 5. Database Migrations
Run Alembic upgrades to set up the data tables:

```bash
alembic upgrade head
```

### 6. Running the Application
Start the FastAPI server via Uvicorn:

```bash
fastapi run app/main.py
# Or run with uvicorn directly
uvicorn app.main:app --reload
```

The API will be accessible at `http://127.0.0.1:8000`. 
Check out the auto-generated API docs at `http://127.0.0.1:8000/docs`.

---

## 🏗️ System Architecture & Flow Diagrams

*Note: The system architectures below are built using Mermaid. If your markdown reader doesn't support them natively, you can view them seamlessly by opening this file on GitHub.*

### 1. High-Level Architecture
This demonstrates how the internal applications, databases, and external APIs communicate with each other.

```mermaid
graph TD
    Client((Client / Browser)) <-->|WebSocket| WS[WebSocket Endpoint <br> /ws/verify]
    Client <-->|REST HTTP| REST[REST Endpoints <br> /detect/*]
    
    subgraph FastAPI Backend
        WS -.-> PipelineService[Fact-Checking Pipeline]
        REST -.-> ValidationLayer[Validation Utils]
        ValidationLayer -.-> AIDetectors[AI Detectors <br> Text, PDF, Image]
        PipelineService -.-> ScraperLayer[Scraping Service]
        PipelineService -.-> FactCheckServices[Claim Extraction <br> Search, Verification]
    end
    
    subgraph Databases
        PipelineService -->|Save Reports <br> AsyncSession| Postgres[(PostgreSQL Database)]
    end

    subgraph External APIs
        AIDetectors <-->|async calls| GeminiAPI[Google Gemini API]
        FactCheckServices <-->|async calls| GeminiAPI
        FactCheckServices <-->|async calls| SearchAPI[DuckDuckGo or Tavily Search API]
        ScraperLayer <-->|HTTP Requests| TargetSites[Target Websites]
    end
```

### 2. WebSocket Fact-Checking Pipeline (Async & Multi-threading)
The core flow of the `/ws/verify` endpoint.

```mermaid
sequenceDiagram
    participant FE as Frontend Client
    participant WS as WebSocket Router
    participant Pipe as Pipeline Service
    participant Scrape as Scraper
    participant AI as AI Detector
    participant LLM as Claims/Verify LLM
    participant Search as Search Agent
    participant DB as PostgreSQL

    FE->>WS: Connect: wss://.../ws/verify
    WS-->>FE: Accept Connection
    FE->>WS: Send JSON payload
    WS->>Pipe: run_pipeline(content)
    
    rect rgb(30, 30, 50)
    Note right of Pipe: Stage 1: Scraping (Threaded)
    Pipe-->>FE: emit stage: scraping
    alt content is URL
        Pipe->>Scrape: asyncio.to_thread(scrape_content)
        Note right of Scrape: Runs blocking I/O<br/>in a separate background thread
        Scrape-->>Pipe: text content
    end
    end

    rect rgb(50, 40, 30)
    Note right of Pipe: Stage 2: Parallel Tasks initiation
    Pipe-->>FE: emit stage: extracting
    Pipe->>AI: asyncio.create_task(detect_ai)
    Note right of AI: AI Detection runs<br/>concurrently in the background
    end

    rect rgb(30, 50, 40)
    Note right of Pipe: Stage 3: Extract & Process Claims
    Pipe->>LLM: extract_claims(text)
    LLM-->>Pipe: list of claims
    loop For each claim
        Pipe-->>FE: emit claim_found event
    end
    
    Pipe-->>FE: emit stage: searching
    Note right of Pipe: Gather all claims and<br/>process them SIMULTANEOUSLY
    par Process Claim 1
        Pipe->>Search: search_for_claim()
        Search-->>Pipe: query, sources
        Pipe-->>FE: emit search_done event
        Pipe->>LLM: verify_claim()
        LLM-->>Pipe: validation verdict
        Pipe-->>FE: emit claim_verified event
    and Process Claim N
        Pipe->>Search: Search for claim query
        Pipe->>LLM: Verify claim
    end
    end

    rect rgb(50, 30, 50)
    Note right of Pipe: Stage 4: Compilation & Database
    Pipe-->>AI: await background AI task
    AI-->>Pipe: ai_probability
    Pipe->>DB: save_report(results, ai_prob)
    DB-->>Pipe: report_id
    Pipe-->>FE: emit report_done event
    end

    opt On Any Exception
        Pipe-->>FE: emit error event
    end
```

### 3. Dedicated AI Detection Endpoints (REST Flow)

```mermaid
flowchart TD
    Req[Client Request] --> Router{Endpoint}

    Router -->|POST /detect/text| TextStart[validate_text]
    Router -->|POST /detect/image| ImgStart[validate_image_file]
    Router -->|POST /detect/pdf| PdfStart[validate_pdf_file]

    TextStart --> DetectText[detect_text_content]
    
    ImgStart --> ImgCheck[PIL Image Verify <br> Check for Corruption]
    ImgCheck -->|Valid| DetectImg[detect_image_content]
    ImgCheck -->|Corrupt| HTTP422[HTTP 422 Error]
    
    PdfStart --> DetectPdf[detect_pdf_content]

    DetectText --> GeminiCall[Call Gemini AI Prompt]
    DetectImg --> GeminiCall
    DetectPdf --> GeminiCall

    GeminiCall --> ParseJSON[Parse LLM JSON Response]
    ParseJSON --> ReturnModel[Return DetectionResult Schema]
    ReturnModel --> Res[Client Response HTTP 200]
```

### 4. WebSocket Error & Event Architecture

```mermaid
stateDiagram-v2
    [*] --> ConnectionAttempt: Client requests WS Protocol
    ConnectionAttempt --> Rejected: Duplicate Session ID
    ConnectionAttempt --> Connected: Session Unique

    state Rejected {
        [*] --> EmitDuplicateError: emit error event
        EmitDuplicateError --> CloseWS
    }

    state Connected {
        [*] --> WaitingForPayload
        WaitingForPayload --> ParsingJSON: Receive data
        ParsingJSON --> InvalidJSON: Fallback to raw text
        ParsingJSON --> ValidatedPayload: Extracted payload
        
        ValidatedPayload --> PipelineExecution: triggers run_pipeline
        InvalidJSON --> PipelineExecution
        
        state PipelineExecution {
           [*] --> EmittingEvents
           EmittingEvents --> SendingUpdates: Emit stage updates
           SendingUpdates --> Done: Emit report_done event
           EmittingEvents --> CatchException: Any unhandled exception
           CatchException --> EmitPipelineError: Emit error event
        }
    }

    Connected --> Disconnected: Client disconnects
    Disconnected --> [*]
```

---

## 🤝 Open Source Details
Factify is completely open source! Feel free to raise issues, submit PRs, and help build a faster, stronger fake-content detection utility. We welcome contributions from the community.
