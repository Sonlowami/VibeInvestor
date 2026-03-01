"""
Utility functions for Gradio UI integration
Handles data formatting, streaming, and memory operations
"""

import pandas as pd
from typing import List, Dict, Any
from logger import logger
from memory import retrieve_top_k
import os
from datetime import datetime

def format_findings_for_table(findings: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert findings list into a formatted DataFrame for Gradio interface
    """
    if not findings:
        return pd.DataFrame(columns=["Company", "Ticker", "Summary", "Metrics"])
    
    rows = []
    for f in findings:
        rows.append({
            "Company": f.get("company_name", "N/A"),
            "Ticker": f.get("ticker", "N/A"),
            "Summary": f.get("summary", "")[:200] + "...",
            "Metrics": str(f.get("metrics", {}))[:150] + "...",
            "Full Summary": f.get("summary", ""),
            "Full Metrics": str(f.get("metrics", {}))
        })
    
    return pd.DataFrame(rows)


def format_metrics_for_display(metrics: Dict[str, float]) -> Dict[str, Any]:
    """
    Format evaluation metrics for gauge chart display
    """
    return {
        "task_completion": round(metrics.get("task_completion", 0) * 100, 1),
        "plan_adherence": round(metrics.get("plan_adherence", 0) * 100, 1),
        "groundedness": round(metrics.get("groundedness", 0) * 100, 1)
    }


def format_groundedness_details(v_res: Dict[str, Any]) -> str:
    """
    Format groundedness verification results for display
    """
    if not v_res or not isinstance(v_res, dict):
        return "Verification data unavailable"
    
    supported = v_res.get("supported_claims", 0)
    total = v_res.get("total_claims", 1)
    score = v_res.get("groundedness_score", 0)
    notes = v_res.get("notes", "")
    
    return f"""
**Verification Summary:**
- Supported Claims: {supported} / {total}
- Groundedness Score: {score:.1%}
- Notes: {notes}
    """.strip()


def format_iteration_trace(iterations: int, feedback_history: List[str]) -> str:
    """
    Format the adaptive iteration trace for display
    """
    trace = f"**Total Iterations:** {iterations}\n\n"
    
    if iterations > 1:
        trace += "**Adaptation Strategy Applied:**\n"
        for i, feedback in enumerate(feedback_history):
            trace += f"- Iteration {i+1}: {feedback}\n"
    else:
        trace += "**Strategy:** Success on first pass"
    
    return trace


def get_memory_summary() -> Dict[str, Any]:
    """
    Get FAISS memory statistics and recent decisions
    """
    db_path = "faiss_investment_db"
    
    summary = {
        "db_exists": os.path.exists(db_path),
        "last_update": None,
        "doc_count": 0,
        "recent_decisions": []
    }
    
    if summary["db_exists"]:
        try:
            mod_time = os.path.getmtime(db_path)
            summary["last_update"] = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
            
            # Try to retrieve top-5 past decisions
            try:
                past_docs = retrieve_top_k("investment opportunity", k=5)
                summary["recent_decisions"] = [
                    d.page_content[:200] for d in past_docs
                ] if past_docs else []
                summary["doc_count"] = len(past_docs) if past_docs else 0
            except Exception as e:
                logger.warning(f"Could not retrieve recent decisions: {e}")
                summary["recent_decisions"] = []
        except Exception as e:
            logger.warning(f"Could not get memory stats: {e}")
    
    return summary


def format_memory_for_display(memory_summary: Dict[str, Any]) -> str:
    """
    Format memory summary for display in UI
    """
    if not memory_summary["db_exists"]:
        return "**Memory Status:** No persistent memory found. Create one by running an analysis."
    
    display = f"""
**Memory Status:** Active ✓
**Last Updated:** {memory_summary['last_update']}
**Total Documents:** {memory_summary['doc_count']}

**Recent Decisions:**
    """.strip()
    
    if memory_summary["recent_decisions"]:
        for i, decision in enumerate(memory_summary["recent_decisions"], 1):
            display += f"\n{i}. {decision}..."
    else:
        display += "\nNo recent decisions logged."
    
    return display


def create_metrics_json(query: str, findings: List[Dict], opportunity: str, iterations: int, metrics: Dict) -> Dict:
    """
    Create a structured JSON output for the full pipeline results
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "findings_count": len(findings),
        "selected_opportunity": opportunity[:100] + "..." if opportunity else "None",
        "iterations": iterations,
        "metrics": metrics,
        "findings_sample": [
            {
                "company": f.get("company_name", "N/A"),
                "ticker": f.get("ticker", "N/A")
            }
            for f in findings[:5]
        ]
    }
