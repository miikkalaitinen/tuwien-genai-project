# Research Paper Navigator

> **TU Wien - Generative AI Course Project (Group 36)**

A "Connection Discovery Engine" that visualizes how research papers relate to each other based on user intent (Student vs Researcher mode).

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- [LlamaCloud API Key](https://cloud.llamaindex.ai/) (for PDF parsing)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API key
echo "LLAMA_CLOUD_API_KEY=your_key_here" > .env
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

## 📦 Testing the PDF Pipeline

### Process All Papers
```bash
cd backend
python -m src.batch_processor
```

### Process Specific Paper
```bash
python -m src.batch_processor --filter "HyperDrive"
```

### Check Data Quality
```bash
python check_quality.py
```

### Inspect Extracted Sections
```bash
cd ..  # Return to project root
python inspect_extraction.py HyperDrive                    # Check methodology
python inspect_extraction.py --section results FOOL        # Check results
python inspect_extraction.py --section abstract --full "Federated"  # Full content
```

---

## 📁 Project Structure

```
backend/
├── app.py                    # FastAPI entry point (Miikka)
├── src/
│   ├── components/
│   │   ├── pdf_ingestion.py  # PDF → Markdown (Jaime) ✅
│   │   ├── chunking.py       # Semantic sections (Jaime) ✅
│   │   ├── connection_engine.py  # LLM relationships (Marta)
│   │   └── graph_builder.py  # Graph data (Miikka)
│   ├── prompts/
│   │   ├── student_prompts.py    # Student mode (Aarne)
│   │   └── researcher_prompts.py # Researcher mode (Aarne)
│   └── utils.py              # Shared utilities (Marta)
├── data/                     # Your PDFs (gitignored)
└── debug_markdowns/          # Raw markdown output (gitignored)

frontend/                     # React + Next.js (Miikka)
```

---

## 👥 Team

| Member | Role | Modules |
|--------|------|---------|
| **Jaime** | Data Pipeline Engineer | `pdf_ingestion.py`, `chunking.py` |
| **Marta** | AI Backend Architect | `connection_engine.py`, `utils.py` |
| **Aarne** | Prompt Engineer & QA | `prompts/`, `tests/evaluation.py` |
| **Miikka** | Frontend Developer | `app.py`, `graph_builder.py`, `frontend/` |
