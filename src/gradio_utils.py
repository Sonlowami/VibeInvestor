"""
Utility functions for Gradio UI integration
Handles data formatting, streaming, and memory operations
"""

import pandas as pd
from typing import List, Dict, Any, Union
from logger import logger
from memory import retrieve_top_k
import os
import re
import json
from datetime import datetime


def format_currency(value: Union[str, int, float]) -> str:
    """
    Format currency values with $ and B/M suffixes for readability
    """
    try:
        # Try to convert to float
        if isinstance(value, str):
            # Remove any existing currency symbols and commas
            clean_value = value.replace('$', '').replace(',', '').strip()
            num_value = float(clean_value)
        else:
            num_value = float(value)
        
        # Format based on magnitude
        if abs(num_value) >= 1_000_000_000:
            # Billions
            formatted = f"${num_value / 1_000_000_000:.2f}B"
        elif abs(num_value) >= 1_000_000:
            # Millions
            formatted = f"${num_value / 1_000_000:.2f}M"
        elif abs(num_value) >= 1_000:
            # Thousands
            formatted = f"${num_value / 1_000:.2f}K"
        else:
            # Less than 1000
            formatted = f"${num_value:.2f}"
        
        return formatted
    except (ValueError, TypeError):
        # If conversion fails, return original value as string
        return str(value)

def format_findings_for_table(findings: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert findings list into a formatted DataFrame for Gradio interface
    """
    if not findings:
        return pd.DataFrame(columns=["Company", "Ticker", "Summary", "Key Metrics", "Financials"])
    
    rows = []
    for f in findings:
        # Format metrics in a readable way
        metrics = f.get("metrics", {})
        metrics_str = ""
        if isinstance(metrics, dict):
            key_metrics = []
            if "pe_ratio" in metrics and metrics["pe_ratio"] != "Not disclosed":
                key_metrics.append(f"P/E: {metrics['pe_ratio']}")
            if "market_cap" in metrics and metrics["market_cap"] != "Not disclosed":
                key_metrics.append(f"Market Cap: {metrics['market_cap']}")
            if "revenue" in metrics and metrics["revenue"] != "Not disclosed":
                key_metrics.append(f"Revenue: {metrics['revenue']}")
            metrics_str = " | ".join(key_metrics) if key_metrics else "Not disclosed"
        else:
            metrics_str = str(metrics) if metrics else "Not disclosed"
        
        # Format financials in a readable way
        financials = f.get("financials", {})
        financials_str = ""
        if isinstance(financials, dict) and financials:
            fin_summary = []
            if "cash_flow" in financials and isinstance(financials["cash_flow"], dict):
                cf = financials["cash_flow"]
                if "Free Cash Flow" in cf:
                    fin_summary.append(f"FCF: {format_currency(cf['Free Cash Flow'])}")
                elif "Operating Cash Flow" in cf:
                    fin_summary.append(f"OCF: {format_currency(cf['Operating Cash Flow'])}")
            if "balance_sheet" in financials and isinstance(financials["balance_sheet"], dict):
                bs = financials["balance_sheet"]
                if "Total Assets" in bs:
                    fin_summary.append(f"Assets: {format_currency(bs['Total Assets'])}")
                if "Total Debt" in bs:
                    fin_summary.append(f"Debt: {format_currency(bs['Total Debt'])}")
            financials_str = " | ".join(fin_summary) if fin_summary else "Available (see details)"
        elif isinstance(financials, str):
            financials_str = financials
        else:
            financials_str = "Not disclosed"
        
        rows.append({
            "Company": f.get("company_name", "N/A"),
            "Ticker": f.get("ticker", "N/A"),
            "Summary": (f.get("summary", "")[:150] + "...") if len(f.get("summary", "")) > 150 else f.get("summary", "N/A"),
            "Key Metrics": metrics_str,
            "Financials": financials_str
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
        "recent_decisions": [],
        "recent_findings": []
    }
    
    if summary["db_exists"]:
        try:
            mod_time = os.path.getmtime(db_path)
            summary["last_update"] = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
            
            # Try to retrieve top-5 past decisions
            try:
                past_docs = retrieve_top_k("investment opportunity", k=5)
                if past_docs:
                    for doc in past_docs:
                        content = doc.page_content
                        # Try to extract structured data from content
                        finding_info = _parse_finding_from_content(content)
                        summary["recent_findings"].append(finding_info)
                    summary["recent_decisions"] = [
                        d.page_content[:200] for d in past_docs
                    ]
                    summary["doc_count"] = len(past_docs)
            except Exception as e:
                logger.warning(f"Could not retrieve recent decisions: {e}")
                summary["recent_decisions"] = []
        except Exception as e:
            logger.warning(f"Could not get memory stats: {e}")
    
    return summary


def _parse_finding_from_content(content: str) -> Dict[str, str]:
    """
    Parse structured data from memory content
    """
    import json
    
    # Try to extract JSON data from content
    try:
        # Look for JSON patterns in content
        json_match = re.search(r'\{[^{}]*"company_name"[^{}]*\}', content)
        if json_match:
            data = json.loads(json_match.group(0))
            return {
                "company": data.get("company_name", "Unknown"),
                "ticker": data.get("ticker", "N/A"),
                "metrics": _format_metrics_simple(data.get("metrics", {})),
                "financials": _format_financials_simple(data.get("financials", {}))
            }
    except:
        pass
    
    # Fallback: return text snippet
    return {"text": content[:200]}


def _format_metrics_simple(metrics: Any) -> str:
    """
    Format metrics dictionary into readable string
    """
    if not isinstance(metrics, dict):
        return "N/A"
    
    parts = []
    for key, value in metrics.items():
        if value and value != "Not disclosed":
            parts.append(f"{key}: {value}")
    
    return ", ".join(parts) if parts else "Not disclosed"


def _format_financials_simple(financials: Any) -> str:
    """
    Format financials dictionary into readable string
    """
    if isinstance(financials, str):
        return financials
    
    if not isinstance(financials, dict) or not financials:
        return "Not disclosed"
    
    parts = []
    
    # Extract key financial data
    if "cash_flow" in financials and isinstance(financials["cash_flow"], dict):
        cf = financials["cash_flow"]
        if "Free Cash Flow" in cf:
            parts.append(f"FCF: {format_currency(cf['Free Cash Flow'])}")
        elif "Operating Cash Flow" in cf:
            parts.append(f"OCF: {format_currency(cf['Operating Cash Flow'])}")
    
    if "balance_sheet" in financials and isinstance(financials["balance_sheet"], dict):
        bs = financials["balance_sheet"]
        if "Total Assets" in bs:
            parts.append(f"Assets: {format_currency(bs['Total Assets'])}")
        if "Total Debt" in bs:
            parts.append(f"Debt: {format_currency(bs['Total Debt'])}")
    
    if "earnings_history" in financials and isinstance(financials["earnings_history"], dict):
        eh = financials["earnings_history"]
        keys = list(eh.keys())
        if keys:
            latest = keys[0]
            parts.append(f"Latest EPS: {eh[latest].get('EPS', 'N/A')}")
    
    return " | ".join(parts) if parts else "Available"


def format_memory_for_display(memory_summary: Dict[str, Any]) -> str:
    """
    Format memory summary for display in UI with human-readable financial data
    """
    if not memory_summary.get("db_exists"):
        return "**Memory Status:** No persistent memory found. Create one by running an analysis."
    
    display = f"""
**Memory Status:** Active ✓
**Last Updated:** {memory_summary.get('last_update', 'Unknown')}
**Total Documents:** {memory_summary.get('doc_count', 0)}

**Recent Findings from Memory:**
    """.strip()
    
    recent_findings = memory_summary.get("recent_findings", [])
    if recent_findings:
        for i, finding in enumerate(recent_findings, 1):
            if "company" in finding:
                display += f"\n\n**{i}. {finding['company']}** ({finding.get('ticker', 'N/A')})\n"
                if "metrics" in finding:
                    display += f"   - Metrics: {finding['metrics']}\n"
                if "financials" in finding:
                    display += f"   - Financials: {finding['financials']}"
            elif "text" in finding:
                display += f"\n{i}. {finding['text']}..."
    else:
        display += "\nNo recent findings in memory."
    
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
