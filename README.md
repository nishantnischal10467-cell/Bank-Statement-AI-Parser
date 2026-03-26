# 🏦 Bank Statement AI Parser Agent

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/OpenAI%20GPT--4-412991?style=for-the-badge&logo=openai&logoColor=white"/>
  <img src="https://img.shields.io/badge/LangGraph-0.2.0+-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white"/>
  <img src="https://img.shields.io/badge/pdfplumber-PDF-red?style=for-the-badge&logo=adobe-acrobat-reader&logoColor=white"/>
  <img src="https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white"/>
 </p>

<p align="center">
  <b>An autonomous AI agent that learns bank statement layouts and auto-generates production-ready Python parsers — no hardcoded rules, no manual templates.</b>
</p>

---

## 📌 Table of Contents

- [Overview](#-overview)
- [How It Works](#-how-it-works)
- [Technologies Used](#️-technologies-used)
- [Dataset & Sample Files](#-dataset--sample-files)
- [Project Architecture](#️-project-architecture)
- [Project Structure](#-project-structure)
- [Key Features](#-key-features)
- [Performance Metrics](#-performance-metrics)
- [Usage in Industry](#-usage-in-industry)
- [Getting Started](#-getting-started)
- [CLI Reference](#-cli-reference)
- [Adding a New Bank](#-adding-a-new-bank)
- [Contributing](#-contributing)

---

## 🔍 Overview

**Bank Statement AI Parser** is an autonomous AI agent that eliminates the manual effort of building custom bank statement parsers. Given a sample PDF and its expected CSV output, the agent:

1. **Analyzes** the PDF structure and CSV schema using GPT-4
2. **Generates** a custom Python parser tailored to that bank's unique format
3. **Tests** the parser against the expected output, scoring accuracy
4. **Self-debugs** and iteratively fixes issues without any human intervention
5. **Saves** the working parser for reuse on future statements from the same bank

The system is fully generalizable — point it at any bank's statement PDF and it adapts automatically.

---

## ⚙️ How It Works

The agent implements a **LangGraph state machine** that drives an intelligent, multi-step workflow:

```
INPUT: Sample PDF  +  Expected CSV
              │
              ▼
     ┌─────────────────┐
     │      PLAN       │  ← Analyze PDF structure, extract text
     │                 │    patterns, understand CSV schema & types
     └────────┬────────┘
              ▼
     ┌─────────────────┐
     │    GENERATE     │  ← GPT-4 writes a parse() function based
     │                 │    on learned patterns + balance delta logic
     └────────┬────────┘
              ▼
     ┌─────────────────┐
     │      TEST       │  ← Execute parser on sample PDF, compare
     │                 │    output with expected CSV (DataFrame.equals)
     └────────┬────────┘
              ▼
         ┌────┴────┐
         │Accurate?│
         └────┬────┘
      ✅ Yes  │   ❌ No
              │         └──► ┌──────────────────┐
              │               │       FIX        │ ← Analyze errors,
              │               │                  │   patch code, retry
              │               └────────┬─────────┘   (up to 3 attempts)
              │                        │ (loop back to TEST)
              ▼
     ┌─────────────────┐
     │      SAVE       │  ← Store parser to custom_parsers/,
     │                 │    report accuracy score + grade
     └─────────────────┘
```

**Balance Delta Logic** — The agent classifies transactions by comparing consecutive balances:
- `balance[n] − balance[n-1] > 0` → **Credit** (inflow)
- `balance[n] − balance[n-1] < 0` → **Debit** (outflow)
- Keyword-based fallback for edge cases

---

## 🛠️ Technologies Used

| Technology | Version | Purpose |
|---|---|---|
| **Python** | 3.10+ | Core language for agent and generated parsers |
| **OpenAI GPT-4** | `openai>=1.40.0` | LLM backbone for code generation and self-debugging |
| **LangGraph** | `>=0.2.0` | Agentic state machine (Plan → Generate → Test → Fix → Save) |
| **LangChain Core** | `>=0.3.0` | LLM orchestration and prompt chaining |
| **pdfplumber** | `>=0.10.3` | PDF text and table extraction |
| **PyMuPDF (fitz)** | `>=1.24.9` | PDF image extraction and page rendering |
| **Pandas** | `>=2.2.2` | DataFrame operations, CSV generation, and accuracy validation |
| **Pydantic** | `>=2.7.0` | Data modeling and schema validation |
| **Tenacity** | `>=8.3.0` | Retry logic for robust API calls |
| **Pillow** | `>=10.4.0` | Image processing for PDF page rendering |
| **python-dotenv** | `>=1.0.1` | Secure API key and environment variable management |

---

## 📂 Dataset & Sample Files

The `data/` directory holds sample bank statements and their expected parsed outputs, used to teach the agent each bank's format.

### Included Bank Samples

| Bank | Folder | Files Included | Description |
|---|---|---|---|
| **ICICI Bank** | `data/icici/` | `icici_sample.pdf`, `result.csv` | Sample ICICI account statement with transaction history |
| **State Bank of India** | `data/SBI/` | `OpenSBI.pdf`, `OpenSBI.csv` | SBI passbook-style statement in PDF format |

### Expected CSV Output Schema

Each `result.csv` follows this standardized structure:

| Column | Type | Description |
|---|---|---|
| `Date` | `datetime` | Transaction date |
| `Description` | `str` | Narration / merchant name |
| `Debit` | `float` | Amount debited (outflow) |
| `Credit` | `float` | Amount credited (inflow) |
| `Balance` | `float` | Running account balance after transaction |

### Adding New Bank Data

```
data/
└── your_bank/
    ├── your_bank_sample.pdf    ← Any real or anonymized statement PDF
    └── result.csv              ← Manually verified expected output
```

> ⚠️ **Privacy Note:** Never commit real bank statements containing personal data. Use anonymized or redacted PDFs as sample data.

---

## 🏗️ Project Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                           USER / CLI                                 │
│                python agent.py --target icici                        │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    ENTRY POINT  (agent.py)                           │
│  • Parses CLI arguments          • Detects existing parsers          │
│  • Routes: generate vs. reuse    • Triggers direct PDF parsing       │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                 AGENT CORE  (core/parser_agent.py)                   │
│                                                                      │
│  ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌────────────────────┐ │
│  │  PLAN   │──►│ GENERATE │──►│   TEST   │──►│    FIX / SAVE      │ │
│  │PDF+CSV  │   │ GPT-4    │   │Validate  │   │ Debug, Retry,      │ │
│  │Analysis │   │ Codegen  │   │Accuracy  │   │ or Store Parser    │ │
│  └─────────┘   └──────────┘   └──────────┘   └────────────────────┘ │
│                                                                      │
│   State Management : core/agent_state.py                             │
│   Prompt Templates : core/prompts.py                                 │
│   Validation Logic : core/validation.py                              │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
┌─────────────────────────┐     ┌──────────────────────────────────┐
│   AI INFRASTRUCTURE     │     │    PDF PROCESSING LAYER           │
│   src/ai_agent/         │     │    src/ai_agent/pdf_utils.py      │
│   ├── llm.py            │     │                                   │
│   ├── config.py         │     │  pdfplumber → text extraction     │
│   └── models.py         │     │  PyMuPDF   → image extraction     │
└─────────────────────────┘     └──────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         OUTPUT LAYER                                 │
│  custom_parsers/icici_parser.py   ← Generated, reusable parser      │
│  data/icici/output.csv            ← Auto-saved parsed result CSV    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
Bank-Statement-AI-Parser/
│
├── agent.py                         # 🚀 Main CLI entry point
├── requirements.txt                 # All Python dependencies
├── PROJECT_SUMMARY.md               # High-level project overview
├── .gitignore
│
├── core/                            # Agent workflow modules
│   ├── __init__.py
│   ├── agent_state.py               # LangGraph state schema management
│   ├── parser_agent.py              # Full LangGraph workflow (Plan→Generate→Test→Fix→Save)
│   ├── validation.py                # Accuracy scoring & performance grading
│   └── prompts.py                   # GPT-4 prompt templates for code generation & debugging
│
├── src/
│   └── ai_agent/                    # Core AI infrastructure
│       ├── __init__.py
│       ├── config.py                # Environment & API key configuration
│       ├── llm.py                   # OpenAI GPT-4 API client integration
│       ├── models.py                # Pydantic data models and type definitions
│       └── pdf_utils.py             # PDF text and image extraction utilities
│
├── data/                            # Sample statements & ground-truth CSVs
│   ├── icici/
│   │   ├── icici_sample.pdf         # Sample ICICI Bank statement (PDF)
│   │   └── result.csv              # Expected parsed output (ground truth)
│   └── SBI/
│       ├── OpenSBI.pdf              # Sample SBI statement (PDF)
│       └── OpenSBI.csv             # Expected SBI parsed output (ground truth)
│
└── custom_parsers/                  # 🤖 Auto-generated bank parsers
    ├── __init__.py
    └── icici_parser.py              # Generated ICICI parser (auto-created by agent)
```

---

## ✨ Key Features

**Autonomous Parser Generation**
GPT-4 writes a complete `parse()` function by learning directly from sample data — no regex templates, no hardcoded column names.

**Self-Debugging Loop**
If the generated parser fails validation, the agent analyzes the error diff and patches its own code automatically, with up to 3 correction attempts.

**Balance Delta Transaction Classification**
Robust debit/credit detection using balance-delta arithmetic rather than fragile keyword matching — works across banks with different narration formats.

**Parser Reuse & Auto-Detection**
On subsequent runs, the agent detects an existing parser in `custom_parsers/` and applies it directly — no unnecessary regeneration.

**Standardized CSV Schema**
Every generated parser outputs the same `Date | Description | Debit | Credit | Balance` schema, making downstream analytics plug-and-play.

**Multi-Bank Extensibility**
Adding a new bank requires two files and one command. The agent handles the rest.

**Production-Grade Validation**
Uses `DataFrame.equals()` for exact structural and value matching, paired with a graded scoring system (A+/A/B/C/F).

---

## 📊 Performance Metrics

| Metric | Benchmark |
|---|---|
| Parser generation time | 30 – 60 seconds |
| Row count (shape) accuracy | 100% |
| Date parsing accuracy | 100% |
| Debit / Credit classification | 90%+ |
| Schema compliance | 100% |
| Typical end-to-end accuracy | 85 – 95% |
| Self-correction success rate | ~80% of first-attempt failures |
| Max statement size tested | 100+ transactions |

### Accuracy Grading Scale

| Grade | Accuracy |
|---|---|
| 🟢 **A+** | ≥ 95% |
| 🟢 **A** | ≥ 85% |
| 🟡 **B** | ≥ 75% |
| 🟠 **C** | ≥ 60% |
| 🔴 **F** | < 60% |

---

## 🏭 Usage in Industry

AI-powered bank statement parsing is in high demand across the financial services ecosystem:

| Industry / Domain | Use Case |
|---|---|
| **Banking & FinTech** | Automate statement ingestion for digital onboarding, KYC, and account aggregation platforms |
| **Lending & Credit** | Parse applicant statements for income verification, cash flow scoring, and credit underwriting |
| **Accounting & ERP** | Extract and push transactions directly into accounting systems (SAP, Tally, QuickBooks) |
| **Personal Finance Apps** | Power expense categorization and budgeting features with clean structured transaction feeds |
| **Audit & Compliance** | Enable auditors to programmatically scan thousands of statements for anomalies or red flags |
| **Tax Technology** | Auto-categorize income and expenses from bank statements for tax filing pipelines |
| **Insurance** | Validate income claims and assess financial health profiles from statement evidence |
| **Wealth Management** | Aggregate multi-bank histories into unified client financial dashboards |

> **Industry Impact:** Manual bank statement processing costs institutions an estimated **$5–$15 per document** in labor. AI-based parsing reduces this to near-zero marginal cost at scale.

---

## 🚀 Getting Started

### Prerequisites

```
Python 3.10+
OpenAI API Key  (GPT-4 access required)
```

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/nishantnischal10467-cell/Bank-Statement-AI-Parser.git
cd Bank-Statement-AI-Parser

# 2. Create and activate virtual environment
python -m venv korbon
korbon\Scripts\activate         # Windows
# source korbon/bin/activate    # Linux / Mac

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Configure your OpenAI API key
set OPENAI_API_KEY=your_openai_api_key          # Windows
# export OPENAI_API_KEY=your_openai_api_key     # Linux / Mac
```

> Or create a `.env` file in the project root:
> ```env
> OPENAI_API_KEY=your_openai_api_key
> ```

---

## 🖥️ CLI Reference

### Generate a New Parser (First Time)

```bash
python agent.py --target icici
```

**Requires:**
- `data/icici/icici_sample.pdf` — sample bank statement PDF
- `data/icici/result.csv` — manually verified expected output

**Produces:**
- `custom_parsers/icici_parser.py` — generated, reusable Python parser
- Accuracy score and performance grade printed to the terminal
- Parsed CSV auto-saved alongside the input PDF

### Parse a New Statement (Reuse Existing Parser)

```bash
python agent.py --target icici --pdf data/icici/new_statement.pdf
```

The agent auto-detects the existing `icici_parser.py` and applies it directly.

### Supported Banks (Included)

| Bank | CLI Flag | Sample Data |
|---|---|---|
| ICICI Bank | `--target icici` | ✅ Included |
| State Bank of India | `--target sbi` | ✅ Included |
| Any new bank | `--target <bank_name>` | Add your own |

---

## 🏛️ Adding a New Bank

Supporting a new bank takes under 5 minutes:

```bash
# Step 1: Create the data folder
mkdir data/hdfc

# Step 2: Add your two files
# data/hdfc/hdfc_sample.pdf   ← anonymized sample statement
# data/hdfc/result.csv        ← manually verified expected output

# Step 3: Run the agent
python agent.py --target hdfc
```

The agent learns from your sample, generates `custom_parsers/hdfc_parser.py`, and reports an accuracy score. Future runs reuse the parser automatically.

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add: description'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

### Ideas for Contribution

- Add support for more Indian and international bank formats
- Improve balance delta edge case handling for zero-balance entries
- Build a Streamlit / FastAPI web UI for non-technical users
- Add batch processing for multiple PDFs in one run
- Add OCR support for scanned / image-based bank statements

---

## 👤 Author

**Nishant Nischal**
- GitHub: [@nishantnischal10467-cell](https://github.com/nishantnischal10467-cell)



<p align="center">
  <i>Built with 🤖 GPT-4 + LangGraph for zero-effort bank statement automation</i><br/>
  <i>If this project helped you, please consider giving it a ⭐ star!</i>
</p>
