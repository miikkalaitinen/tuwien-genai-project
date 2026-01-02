# Research Paper Navigator

> **TU Wien - Generative AI Course Project (Group 36)**

A "Connection Discovery Engine" that visualizes how research papers relate to each other based on user intent (Student vs Researcher mode).

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- [LlamaCloud API Key](https://cloud.llamaindex.ai/) (for PDF parsing)
- [Groq API Key](https://console.groq.com/keys) (for LLM - free tier available)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys (copy from template)
cp .env.example .env
# Then edit .env with your actual keys
```

### Add PDFs to Process

Place your research papers in `backend/data/`:
```
backend/data/
├── paper1.pdf
├── paper2.pdf
└── ...
```

---

## 📦 Pipeline Usage

### Step 1: Process PDFs → Structured JSON
```bash
cd backend
python -m src.batch_processor --data-dir data/ --output processed_papers.json --verbose
```

This extracts text from PDFs and splits into semantic sections (abstract, introduction, methodology, etc.)

### Step 2: Generate Relationship Graph
```bash
python -m src.integration -o paper_graph.json -l 5
```

Options:
- `-o, --output`: Output file path (default: `paper_graph.json`)
- `-l, --limit`: Limit number of papers to process (useful for testing)
- `-i, --input`: Input JSON file (default: `processed_papers.json`)

### Additional Commands

**Process specific paper:**
```bash
python -m src.batch_processor --filter "HyperDrive"
```

**Check data quality:**
```bash
python check_quality.py
```

**Inspect extracted sections:**
```bash
cd ..  # Return to project root
python inspect_extraction.py HyperDrive                    # Check methodology
python inspect_extraction.py --section results FOOL        # Check results
python inspect_extraction.py --section abstract --full "Federated"  # Full content
```

**Run integration tests:**
```bash
python test_integration.py
```

---

## 🔄 Data Flow

```
┌─────────────┐    ┌─────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│  PDF Files  │───▶│ LlamaParse  │───▶│  Semantic Chunking   │───▶│ processed_      │
│  (data/)    │    │  API        │    │  (sections)          │    │ papers.json     │
└─────────────┘    └─────────────┘    └──────────────────────┘    └────────┬────────┘
                                                                           │
                                                                           ▼
┌─────────────┐    ┌─────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│  React Flow │◀───│  FastAPI    │◀───│  Relationship        │◀───│ Integration     │
│  (frontend) │    │  Endpoints  │    │  Synthesis (LLM)     │    │ Module          │
└─────────────┘    └─────────────┘    └──────────────────────┘    └─────────────────┘
```

---

## 📁 Project Structure

```
backend/
├── app.py                    # FastAPI entry point (Miikka) ⏳
├── src/
│   ├── batch_processor.py    # Batch PDF processing CLI (Jaime) ✅
│   ├── integration.py        # Pipeline → Graph bridge (Jaime) ✅
│   ├── utils.py              # LLM, ChromaDB, schemas (Marta) ✅
│   ├── components/
│   │   ├── pdf_ingestion.py  # PDF → Markdown (Jaime) ✅
│   │   ├── chunking.py       # Semantic sections (Jaime) ✅
│   │   ├── connection_engine.py  # LLM relationships (Marta) ✅
│   │   └── graph_builder.py  # Graph data (Miikka) ⏳
│   └── prompts/
│       ├── student_prompts.py    # Student mode (Aarne) ⏳
│       └── researcher_prompts.py # Researcher mode (Aarne) ⏳
├── data/                     # Your PDFs (gitignored)
├── processed_papers.json     # Extracted paper data
└── .env.example              # API key template

frontend/                     # React + Next.js (Miikka)
├── app/
│   ├── components/
│   │   ├── GraphCanvas.tsx   # React Flow visualization ⏳
│   │   └── Sidebar.tsx       # Mode toggle & upload ⏳
│   └── page.tsx
└── package.json
```

---

## 🔑 API Keys Required

| Key | Purpose | Get it at |
|-----|---------|-----------|
| `LLAMA_CLOUD_API_KEY` | PDF parsing | [cloud.llamaindex.ai](https://cloud.llamaindex.ai/) |
| `GROQ_API_KEY` | LLM (Llama 3.1) | [console.groq.com](https://console.groq.com/keys) |
| `GOOGLE_API_KEY` | Gemini fallback (optional) | [aistudio.google.com](https://aistudio.google.com/) |

---

## 👥 Team

| Member | Role | Modules | Status |
|--------|------|---------|--------|
| **Jaime** | Data Pipeline Engineer | `pdf_ingestion.py`, `chunking.py`, `batch_processor.py`, `integration.py` | ✅ Complete |
| **Marta** | AI Backend Architect | `connection_engine.py`, `utils.py` | ✅ Complete |
| **Aarne** | Prompt Engineer & QA | `prompts/`, `tests/evaluation.py` | ⏳ In Progress |
| **Miikka** | Frontend Developer | `app.py`, `graph_builder.py`, `frontend/` | ⏳ In Progress |

---

## 📤 Output Format

The `paper_graph.json` output is compatible with React Flow:

```json
{
  "nodes": [
    {
      "id": "paper_0",
      "type": "default",
      "position": {"x": 0, "y": 0},
      "data": {
        "label": "Paper Title",
        "methodology": "Experimental study",
        "key_result": "Main finding",
        "core_theory": "Theoretical framework"
      }
    }
  ],
  "edges": [
    {
      "id": "edge_0_1",
      "source": "paper_0",
      "target": "paper_1",
      "label": "Extends",
      "data": {
        "relation_type": "Extends",
        "confidence": 0.85,
        "explanation": "Paper B extends the methodology of Paper A..."
      }
    }
  ]
}
```
