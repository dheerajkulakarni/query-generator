# Query Generator

> **AI-powered database query generator** — Store your database schemas and generate SQL/NoSQL queries from plain English using LLMs.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Gradio](https://img.shields.io/badge/UI-Gradio-orange?logo=gradio)
![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-green)
![OpenAI Compatible](https://img.shields.io/badge/LLM-OpenAI%20Compatible-blueviolet)

---

## ✨ Features

- **Multi-database support** — PostgreSQL, MySQL, SQLite, MongoDB, SQL Server, Oracle, and more
- **Natural-language to query** — Describe what you want in plain English, get the correct query
- **Schema-aware generation** — Stores schemas in a vector database for accurate, context-aware results
- **Smart filtering** — Filter by application, database name, and database type to ensure only relevant tables are used
- **Pluggable architecture** — Easily swap LLM providers and vector databases
- **Copy-friendly output** — Syntax-highlighted queries with one-click copy

---

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone https://github.com/your-username/query-generator.git
cd query-generator

python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure your API key

```bash
cp .env.example .env
# Edit .env and set your LLM API key
```

For **Google Gemini**, get a key from [Google AI Studio](https://aistudio.google.com/apikey) and set:
```
LLM_API_KEY=your-gemini-api-key
```

### 3. Run

```bash
python main.py
```

Open **http://localhost:7860** in your browser.

---

## 📖 How to Use

### Step 1: Add Your Schemas

Go to the **📋 Add Schema** tab and fill in:

| Field | Description | Example |
|-------|-------------|---------|
| **Application Name** | Your project/app name | `my_ecommerce_app` |
| **Database Type** | SQL dialect or DB engine | `PostgreSQL` |
| **Database Name** | Actual database name | `ecommerce_db` |
| **Table Name** | Table or collection name | `users` |
| **Schema Definition** | Paste your `CREATE TABLE`, JSON schema, etc. | See below |

**Example schema input:**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

Add as many tables as you need. Repeat for `orders`, `products`, etc.

### Step 2: Generate Queries

Go to the **⚡ Generate Query** tab:

1. **Type your question** in plain English — e.g., _"Get the total number of users who signed up in the last 30 days"_
2. **Set filters** — Application Name, Database Name, Database Type
3. Click **🚀 Generate Query**
4. Copy the generated query from the syntax-highlighted output

---

## 🏗️ Understanding App Name & Database Name

These fields solve a real-world problem: **schema disambiguation**.

### Why Database Name matters

> Tables can only be `JOIN`ed if they're in the **same database**.

If you have a `users` table in both `ecommerce_db` and `analytics_db`, specifying the database name ensures the generator only uses relevant tables as context.

### Why Application Name matters

> Different applications can have databases with the **same name**.

For example, your staging and production environments might both have a database called `main_db`. The application name (`staging_app` vs `prod_app`) keeps them separate.

### Hierarchy

```
Application (e.g., my_ecommerce_app)
  └── Database (e.g., ecommerce_db)
        └── Table (e.g., users, orders, products)
```

Both fields default to `"default"`, so you can ignore them for simple, single-app use cases.

---

## 🔄 How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                        User Input                           │
│  "Get total revenue by product category for last quarter"   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              1. Schema Retrieval (ChromaDB)                  │
│                                                             │
│  • User's question is converted to an embedding             │
│  • Cosine similarity finds the most relevant schemas        │
│  • Filters applied: app_name → db_name → db_type            │
│  • Returns top matching table schemas                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              2. Prompt Construction                          │
│                                                             │
│  System prompt (expert query generator rules)               │
│  + Retrieved schemas (CREATE TABLE statements)              │
│  + User's natural-language question                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              3. LLM Query Generation                         │
│                                                             │
│  • Sends prompt to LLM (Gemini / OpenAI / Ollama)           │
│  • LLM generates the exact query using correct table/column │
│    names and the right SQL dialect                           │
│  • Response is cleaned (markdown fences stripped)            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              4. Output                                       │
│                                                             │
│  SELECT c.name AS category, SUM(oi.quantity * oi.price)     │
│  FROM order_items oi                                        │
│  JOIN products p ON oi.product_id = p.id                    │
│  JOIN categories c ON p.category_id = c.id                  │
│  WHERE oi.created_at >= NOW() - INTERVAL '3 months'         │
│  GROUP BY c.name;                                           │
└─────────────────────────────────────────────────────────────┘
```

**Key insight:** The vector database doesn't generate queries — it finds which schemas are relevant. The LLM does the actual query writing using those schemas as context.

---

## 📁 Project Structure

```
query-generator/
├── main.py                      # Entry point — wires up all components
├── config.yaml                  # Default configuration
├── .env.example                 # Environment variables template
├── requirements.txt
├── app/
│   ├── config/
│   │   └── settings.py          # Pydantic settings (YAML + env vars)
│   ├── vectordb/
│   │   ├── base.py              # Abstract VectorStore interface
│   │   └── chroma_store.py      # ChromaDB implementation
│   ├── llm/
│   │   ├── base.py              # Abstract LLMProvider interface
│   │   └── llm_provider.py      # OpenAI-compatible implementation
│   ├── core/
│   │   ├── schema_manager.py    # Schema CRUD + search
│   │   └── query_generator.py   # Orchestrates retrieval + LLM
│   └── ui/
│       └── gradio_app.py        # Gradio web interface
└── tests/
    ├── test_schema_manager.py
    └── test_query_generator.py
```

---

## ⚙️ Configuration

### config.yaml

```yaml
llm:
  provider: gemini          # gemini | openai | ollama
  model: gemini-2.5-flash
  temperature: 0.1

vectordb:
  provider: chroma
  persist_directory: ./chroma_data
  collection_name: schemas

app:
  host: "0.0.0.0"
  port: 7860
  share: false
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `LLM_API_KEY` | API key for your LLM provider | ✅ (cloud providers) |
| `LLM_MODEL` | Override model name | ❌ |
| `LLM_TEMPERATURE` | Sampling temperature (0–2) | ❌ |
| `LLM_BASE_URL` | Custom API endpoint | ❌ |
| `VECTORDB_PERSIST_DIR` | ChromaDB storage path | ❌ |
| `VECTORDB_COLLECTION` | Collection name | ❌ |

### Switching LLM Providers

```yaml
# Google Gemini (default)
llm:
  provider: gemini
  model: gemini-2.5-flash

# OpenAI
llm:
  provider: openai
  model: gpt-4o

# Local Ollama
llm:
  provider: ollama
  model: llama3
```

---

## 🧑‍💻 Development

### Prerequisites

- Python 3.10+
- An LLM API key (Gemini, OpenAI) or a local Ollama instance

### Setup

```bash
# Clone and create venv
git clone https://github.com/your-username/query-generator.git
cd query-generator
python -m venv venv
venv\Scripts\activate  # or source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API key
```

### Running Tests

```bash
pytest tests/ -v
```

Tests use a real in-memory ChromaDB instance and a mock LLM provider — no API keys needed.

### Adding a New LLM Provider

1. Create `app/llm/your_provider.py`
2. Implement the `LLMProvider` interface:
   ```python
   from app.llm.base import LLMProvider

   class YourProvider(LLMProvider):
       def generate(self, prompt: str, system_prompt: str = "") -> str:
           ...
   ```
3. Wire it up in `main.py`

### Adding a New Vector Database

1. Create `app/vectordb/your_store.py`
2. Implement the `VectorStore` interface:
   ```python
   from app.vectordb.base import VectorStore

   class YourStore(VectorStore):
       def add(self, document_id, text, metadata): ...
       def search(self, query, top_k=3): ...
       def delete(self, document_id): ...
       def list_all(self): ...
   ```
3. Wire it up in `main.py`