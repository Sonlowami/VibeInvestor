# VibeInvestor Gradio UI Guide

## Overview

VibeInvestor now includes an intuitive web-based interface built with **Gradio**, allowing you to:
- 🔍 **Discover** investment opportunities in real-time
- ⚖️ **Analyze** the governor's decision and reasoning
- 📊 **Monitor** system metrics and long-term memory integration
- 🧠 **Inspect** past decisions and adaptive strategies

---

## Quick Start

### macOS / Linux
```bash
cd /path/to/VibeInvestor
./launch_ui.sh
```

### Windows
```cmd
cd C:\path\to\VibeInvestor
launch_ui.bat
```

### Manual Launch (Any OS)
```bash
cd src
python3 gradio_app.py
```

The UI will be available at **http://localhost:7860**

---

## Prerequisites

Before launching, ensure:

1. **Python 3.12+** is installed
2. **Dependencies installed**:
   ```bash
   pip install -r requirements.txt
   ```

3. **.env file configured** with API keys:
   ```
   GOOGLE_API_KEY=your_google_api_key
   SEARCHAPI_KEY=your_searchapi_key
   ```

---

## Interface Structure

### Tab 1: 🔍 Discovery Engine

This is where you watch the Finder agent discover opportunities in real-time.

**Input:**
- **Investment Query**: Describe what you're looking for
  - Example: *"Find undervalued AI companies in healthcare with positive cash flow"*

**Real-Time Outputs:**

- **Status**: Current operation (Finding → Memory → Governor Decision → Verification)
- **Iteration Counter**: Shows progress (e.g., "1/3")
- **Live Logs**: Stream of all agent actions
  - `[Finder]` - Web search and extraction
  - `[Memory]` - FAISS vector database updates
  - `[Governor]` - Decision-making
  - `[Verifier]` - Groundedness checking
  - `[Adaptive]` - Strategy adjustments

- **Adaptive Strategy**: Shows the current strategy if system is iterating
  - Example: *"Find more primary evidence for these specific claims"*

- **Discovered Opportunities Table**: Lists all findings with:
  - Company name
  - Ticker symbol
  - Summary (truncated, hover for full text)
  - Key metrics

---

### Tab 2: ⚖️ Decision Analysis

Displays the Governor's final selection and the Verifier's groundedness analysis.

**Selected Opportunity:**
- Full text of the governor's chosen opportunity
- Includes executive summary, key evidence, and strategic alignment

**Verification Breakdown:**
- **Supported Claims / Total Claims**: Ratio of evidence-backed statements
- **Groundedness Score**: 0-100% confidence in the decision
- **Verification Notes**: Explanation of any evidence gaps

**Example Output:**
```
Verification Summary:
- Supported Claims: 4 / 5
- Groundedness Score: 84.0%
- Notes: Primary revenue stream well-documented; geographic 
  expansion claims need secondary sources
```

---

### Tab 3: 📊 Metrics & Memory

System-level performance monitoring and memory inspection.

**Performance Metrics (Live Charts):**
- **Task Completion**: Did the system find a valid opportunity? (0-100%)
- **Plan Adherence**: Does the result match the original query? (0-100%)
- **Groundedness**: Is the decision well-supported by evidence? (0-100%)

**Adaptive Iteration Trace:**
Shows how many iterations were required and why:
```
Total Iterations: 2

Adaptation Strategy Applied:
- Iteration 1: Targeted re-discovery for evidence
```

If successful on first try:
```
Strategy: Success on first pass
```

**Persistent Memory Status:**
- **Memory Status**: Active ✓ or Empty
- **Last Updated**: Timestamp of last analysis
- **Total Documents**: Number of findings indexed
- **Recent Decisions**: Snippet of past opportunities analyzed

**Clear Memory Button:**
Wipes the FAISS vector database if you want a fresh start.

---

## Workflow Example

### Scenario: Finding Healthcare AI Companies

**Step 1: Enter Query**
```
Find AI-powered healthcare companies with positive cash flow 
and less than $2B market cap
```

**Step 2: Watch Discovery**
- Watch the Finder crawl the web for 10-15 seconds
- See real-time logs showing extracted companies
- Monitor the Findings table populate

**Step 3: System Decides**
- Governor ranks all findings and selects the best match
- If groundedness < 70%, system auto-adapts:
  - Iteration 2 shown in status
  - New strategy applied (e.g., "Find more primary evidence")
  - Reruns discovery with refined query

**Step 4: Review Results**
- Switch to **Decision Analysis** tab
- Read why this company was selected
- Check verification score (is it well-supported?)

**Step 5: Monitor System**
- Switch to **Metrics & Memory** tab
- See Task Completion %, Plan Adherence %, Groundedness %
- If this is your 2nd+ run, review past decisions in memory

**Step 6: Next Steps**
- Export findings for manual research
- Refine your query if result wasn't quite right
- Clear memory if you want a completely fresh analysis

---

## Advanced Tips

### 1. Iterative Refinement
If the system iterates (shows "Iteration 2/3"), you're seeing adaptive refinement in action. The system is:
- Detecting low groundedness
- Adjusting search constraints
- Re-running discovery with new strategy

This is **intentional** — it ensures high-quality results.

### 2. Memory Integration
Your discoveries are stored in FAISS (vector database):
- Persists across sessions
- Influences future analyses via semantic search
- Can be cleared anytime via the **Clear Memory** button

### 3. Log Interpretation
```
[Finder] Discovered 12 findings. Sample companies: ACME Corp, TechStart Inc, MediAI Labs
[Governor] Selected opportunity: MediAI Labs emerging...
[Verifier] Groundedness Score: 87.3%
[Adaptive] Success threshold met.
```

- ✓ `Success threshold met` = Done (Completion ≥100%, Groundedness ≥70%)
- 🔄 `Low groundedness` = Iteration with targeted evidence search
- 🔄 `Incomplete results` = Iteration with broader search

---

## Troubleshooting

### UI won't load
- Check that Gradio is installed: `pip install gradio>=5.0.0`
- Ensure port 7860 is not in use (check `lsof -i :7860` on Mac/Linux)
- Try a different port: `python3 src/gradio_app.py --server_port 7861`

### No findings discovered
- Check your GOOGLE_API_KEY and SEARCHAPI_KEY are valid
- Try a simpler query (e.g., "tech companies")
- Check internet connectivity

### Memory errors
- Clear memory with the button in Metrics tab
- Restart the UI: `Ctrl+C` and relaunch

### Slow execution
- System may be iterating (1-3 iterations normal)
- Each iteration takes 15-30 seconds
- Watch the logs to understand what's happening

---

## Architecture (For Developers)

The Gradio UI is built on:

| Component | File | Purpose |
|-----------|------|---------|
| **Main App** | `src/gradio_app.py` | Gradio interface & event handlers |
| **Utils** | `src/gradio_utils.py` | Data formatting & memory helpers |
| **Pipeline** | `src/main.py` | Core agent logic (unchanged) |
| **Agents** | `src/finder.py`, `src/governor.py`, etc. | Individual agent implementations |
| **Memory** | `src/memory.py` | FAISS vector DB operations |

The UI uses **async streaming** to display real-time updates without blocking.

---

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Clear input | `Ctrl+A` → Delete |
| Copy logs | Highlight text → `Ctrl+C` |
| Stop long-running query | `Ctrl+C` in terminal |

---

## Known Limitations

1. **Single Query at a Time**: Can't run multiple analyses simultaneously
2. **File Export**: PDF export coming in next release
3. **Mobile Support**: Best viewed on desktop (tablet partially supported)
4. **Session Timeout**: Long-running queries may timeout after 5 minutes

---

## Next Steps

- Run your first analysis with a sample query
- Explore the logs to understand agent reasoning
- Check memory integration across multiple runs
- Fine-tune your queries based on results

---

Questions? See the main [README.md](../README.md) for project overview and architecture details.
