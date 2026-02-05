# VibeInvestor

VibeInvestor is an experimental agentic system that continuously scans the web for emerging opportunities, filters them through lightweight evidence checks, and surfaces only those that are *worth a human’s attention*.

It is not a trading bot.  
It does not make investments.  
It does not optimize portfolios.

Instead, VibeInvestor acts like a disciplined research assistant: reading broadly, cross-checking claims, and escalating only well-supported signals for further analysis.

## What Problem Is VibeInvestor Solving?

Modern investment signals are noisy, fragmented, and time-sensitive. Valuable information often appears first in press releases, niche publications, regulatory filings, or company announcements — long before it shows up in polished analyst reports.

VibeInvestor is designed to:
- Detect early signals from public information
- Check for evidences
- Prevent low-quality or speculative claims from reaching decision-makers
- Create a structured trail of *why* something was flagged

The goal is not speed alone, but **signal quality under uncertainty**.

## Core Philosophy

VibeInvestor is built on a few simple ideas:

- **Agents should reason procedurally, not magically**  
  Each agent follows explicit, explainable steps rather than opaque “intuition.”

- **Evidence before opinion**  
  Claims are surfaced only after basic cross-source validation and credibility assessment.

- **Automation with guardrails**  
  The system is allowed to explore, but within clearly defined constraints and feedback loops.

- **Humans stay in the loop**  
  Final decisions are escalated to a human, not executed automatically.

## What VibeInvestor Is (and Is Not)

VibeInvestor *is*:
- A multi-agent research pipeline
- A structured opportunity discovery system
- A closed-loop architecture with memory and feedback
- A platform for experimenting with agent governance and tooling

VibeInvestor is *not*:
- A financial advisor
- A prediction engine
- A reinforcement-learning trader
- A replacement for human judgment

## High-Level Architecture (Conceptual)

At a high level, VibeInvestor consists of:

- **Finder agents** that search the web and extract candidate opportunities
- **Analyst agents** that independently evaluate those opportunities using different assumptions
- **A governor** that arbitrates between analyses and decides what to escalate
- **A shared memory layer** that records decisions, feedback, and outcomes
- **A tool layer** (e.g., web search, code execution, email) accessed via explicit contracts
- **A closed feedback loop** that allows the system to improve over time

Every cycle follows the same pattern:

**Observe → Reason → Decide → Act → Update → Repeat**

## Why “Vibe” Investor?

Because early-stage signals are rarely clean or complete.

VibeInvestor is about capturing *structured vibes* — emerging narratives, early evidence, and directional signals — while being honest about uncertainty, confidence, and limitations.

It doesn’t chase certainty.  
It curates plausibility.

---

This project is a work in progress and an exploration of how far careful system design can go before “intelligence” becomes the bottleneck.
## Getting Started

### Prerequisites

- Python 3.12+ (required for compatibility with vector database dependencies)
- `pip` package manager
- API keys for:
  - **Google Gemini API** (for LLM access) — Get from [Google AI Studio](https://aistudio.google.com/apikey)
  - **SearchAPI.io** (for web search) — Get from [SearchAPI.io](https://www.searchapi.io/)

### Installation

1. **Clone the repository** (if not already done):
   ```bash
   cd /Users/oswaldocamillegrimaud/Desktop/VibeInvestor
   ```

2. **Create a Python 3.12 virtual environment**:
   ```bash
   python3.12 -m venv .venv-py312
   ```

3. **Activate the virtual environment**:
   ```bash
   source .venv-py312/bin/activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

1. **Create a `.env` file** in the project root (if not already present):
   ```bash
   cp .env.example .env  # or create it manually
   ```

2. **Add your API keys** to `.env`:
   ```
   GOOGLE_API_KEY=<your-google-api-key>
   SEARCHAPI_KEY=<your-searchapi-key>
   GROQ_API_KEY=<optional-groq-api-key>
   ```

   - **GOOGLE_API_KEY**: Get from [Google AI Studio](https://aistudio.google.com/apikey)
   - **SEARCHAPI_KEY**: Get from [SearchAPI.io dashboard](https://www.searchapi.io/dashboard)

### Running the Project

**Basic execution** (with Python 3.12 environment activated):

```bash
python src/main.py
```

**Or, using the venv directly without activation**:

```bash
.venv-py312/bin/python src/main.py
```

### What Happens When You Run It

1. **Finder Agent** searches the web for undervalued stocks and emerging opportunities
2. **Results** are extracted and stored in a FAISS vector database for memory
3. **Governor Agent** evaluates findings and surfaces the most promising opportunities
4. **Output** is printed to the console

### Project Structure

```
VibeInvestor/
├── src/
│   ├── finder.py          # Finder agent: web search & opportunity discovery
│   ├── governor.py        # Governor agent: arbitrates & escalates decisions
│   ├── retriever.py       # Memory retrieval for context
│   ├── memory.py          # Vector database (FAISS) management
│   ├── prompts.py         # Agent task definitions
│   ├── utils.py           # Shared utilities (JSON parsing, PDF generation)
│   ├── main.py            # Entry point: orchestrates the agent pipeline
│   └── __init__.py
├── .env                   # API keys (create this file)
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

### Troubleshooting

**Issue**: `GOOGLE_API_KEY not found`
- **Solution**: Ensure `.env` file exists in the project root and contains `GOOGLE_API_KEY=<your-key>`

**Issue**: Python version incompatibility
- **Solution**: Use Python 3.12 explicitly: `python3.12 -m venv .venv-py312`

**Issue**: Package import errors
- **Solution**: Ensure virtual environment is activated and dependencies are installed:
  ```bash
  source .venv-py312/bin/activate
  pip install -r requirements.txt
  ```

**Issue**: `IndexError: list index out of range` in memory.py
- **Solution**: This occurs when the Finder returns empty results. Check that:
  1. API keys are valid
  2. Web search is returning results
  3. LLM is formatting output as valid JSON

### Development Notes

- The system uses **Gemini 2.0 Flash** as the default LLM
- Vector storage uses **FAISS** with **Google Generative AI Embeddings**
- Web search is powered by **SearchAPI.io**
- Memory is persisted locally in `faiss_investment_db/` directory

---

### Contributions

**Oswaldo Camille Grimaud**
- Conceptualized the VibeInvestor system architecture and core philosophy
- Designed the multi-agent pipeline (Finder → Governor → Memory loop)
- Implemented the Finder agent with web search integration
- Built the Governor agent for opportunity arbitration and decision escalation
- Developed the FAISS vector database memory layer
- Created agent prompts and task definitions (FINDER_TASK, GOVERNOR_TASK)
- Orchestrated the main pipeline and agent coordination
- Integrated API connections (Google Gemini, SearchAPI.io)

**Lowami**
- Debugged and resolved critical LLM compatibility issues with browser-use
- Investigated and resolved Python 3.14/3.12 environment conflicts
- Troubleshot Chroma/pydantic dependency incompatibilities
- Fixed API key configuration and environment loading
- Implemented robust JSON parsing with fallback error handling in `extract_json()`
- Enhanced prompt engineering to enforce proper JSON output formatting
- Created comprehensive setup and troubleshooting documentation
- Established development environment best practices

---
