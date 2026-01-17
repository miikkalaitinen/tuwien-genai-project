# Research Paper Navigator

> **TU Wien - Generative AI Course Project (Group 36)**

A "Connection Discovery Engine" that visualizes how research papers relate to each other based on user intent (Student vs Researcher mode).

## ✨ Features

- **📄 PDF Upload** - Drag & drop research papers for automatic processing
- **🔍 Two Modes**:
  - **Student Mode** - Conceptual bridging with educational explanations
  - **Researcher Mode** - Rigorous technical analysis with causal chains
- **🕸️ Interactive Graph** - Color-coded relationship visualization:
  - 🟢 Green = Supports
  - 🔴 Red = Contradicts
  - 🔵 Blue = Extends
- **💡 Click-to-Explore** - View paper details and relationship explanations

---

## 🚀 Quick Start

### Prerequisites
- Docker Desktop
- [LlamaCloud API Key](https://cloud.llamaindex.ai/) (for PDF parsing)
- [Groq API Key](https://console.groq.com/keys) (for LLM - free tier available)

### Setup

```bash
# Clone and configure
git clone https://github.com/miikkalaitinen/tuwien-genai-project
cd tuwien-genai-project

# Set up API keys
cp backend/.env.example backend/.env
# Edit backend/.env with your keys

# Run with Docker Compose
docker compose up --build
```

Then open **http://localhost:3000** in your browser.

---

## 🎯 How to Use

1. **Upload PDFs** - Use the sidebar to upload your research papers
2. **Select Mode** - Choose between Student (educational) or Researcher (technical)
3. **Generate Graph** - Click "Generate" to process papers and build relationships
4. **Explore** - Click on nodes to see paper details, edges to see explanations
5. **Switch Modes** - Toggle mode and regenerate to see different relationship perspectives

---

## 📁 Project Structure

```
backend/
├── app.py                    # FastAPI server with async job processing
├── src/
│   ├── batch_processor.py    # Batch PDF processing CLI
│   ├── integration.py        # Pipeline → Graph bridge
│   ├── utils.py              # LLM, ChromaDB, schemas
│   ├── components/
│   │   ├── pdf_ingestion.py  # PDF → Markdown (LlamaParse)
│   │   ├── chunking.py       # Semantic section extraction
│   │   └── connection_engine.py  # LLM relationship synthesis
│   └── prompts/
│       ├── student_prompts.py    # Academic tutor persona
│       └── researcher_prompts.py # Principal investigator persona
├── local_models/             # Local HuggingFace embedding model
├── chroma_db/                # Vector store for embeddings
└── .env.example              # API key template

frontend/
├── app/
│   ├── page.tsx              # Main application page
│   ├── types.ts              # TypeScript interfaces
│   └── components/
│       ├── GraphCanvas.tsx   # ReactFlow visualization
│       ├── Sidebar.tsx       # Upload & mode controls
│       ├── NodeModal.tsx     # Paper details popup
│       ├── EdgeModal.tsx     # Relationship details popup
│       ├── CustomEdge.tsx    # Color-coded edge rendering
│       └── ErrorBanner.tsx   # Toast notifications
├── Dockerfile
└── package.json

docker-compose.yml            # One-command deployment
```

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                            FRONTEND (Next.js)                            │
│  ┌───────────┐  ┌─────────────┐  ┌───────────┐  ┌───────────────────┐    │
│  │  Sidebar  │  │ GraphCanvas │  │ NodeModal │  │     EdgeModal     │    │
│  │ (Upload)  │  │ (ReactFlow) │  │ (Details) │  │  (Relationships)  │    │
│  └─────┬─────┘  └──────▲──────┘  └───────────┘  └───────────────────┘    │
└────────┼───────────────┼──────────────────────────────────────────────── ┘
         │ POST /process-batch    │ GET /batch-status
         ▼                        │
┌──────────────────────────────────────────────────────────────────────────┐
│                           BACKEND (FastAPI)                              │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                       Async Job Processing                         │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────────────┐    │  │
│  │  │ LlamaParse  ─▶  Chunking   ─▶    Connection Engine        │    │  │
│  │  │ (PDF→Text) │  │ (Sections) │  │   (LLM Relationships)      │    │  │
│  │  └────────────┘  └────────────┘  └────────────────────────────┘    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                   │                                      │
│             ┌─────────────────────┼─────────────────────┐                │
│             ▼                     ▼                     ▼                │
│  ┌────────────────┐  ┌────────────────────┐  ┌────────────────┐          │
│  │ Student Prompts│  │ Researcher Prompts │  │    ChromaDB    │          │
│  │  (Conceptual)  │  │    (Technical)     │  │  (Embeddings)  │          │
│  └────────────────┘  └────────────────────┘  └────────────────┘          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 🔑 API Keys Required

| Key | Purpose | Get it at |
|-----|---------|-----------|
| `LLAMA_CLOUD_API_KEY` | PDF parsing | [cloud.llamaindex.ai](https://cloud.llamaindex.ai/) |
| `GROQ_API_KEY` | LLM (Llama 3.1) | [console.groq.com](https://console.groq.com/keys) |
| `GOOGLE_API_KEY` | Embeddings (optional - local fallback available) | [aistudio.google.com](https://aistudio.google.com/) |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 16, React 19, ReactFlow, Tailwind CSS |
| **Backend** | Python 3.10, FastAPI, LlamaIndex |
| **LLM** | Groq (Llama 3.1 70B) |
| **Embeddings** | HuggingFace (all-MiniLM-L6-v2) / Google Gemini |
| **Vector Store** | ChromaDB |
| **PDF Parsing** | LlamaParse |
| **Deployment** | Docker Compose |

---

## 👥 Team

| Member | Role | Contributions |
|--------|------|---------------|
| **Jaime** | Data Pipeline Engineer | PDF ingestion, chunking, batch processor, integration |
| **Marta** | AI Backend Architect | Connection engine, RAG functions, ChromaDB integration |
| **Aarne** | Prompt Engineer | Student & researcher prompts, evaluation |
| **Miikka** | Full-Stack Developer | FastAPI server, frontend, Docker setup |
