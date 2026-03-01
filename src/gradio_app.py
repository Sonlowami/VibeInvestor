"""
Gradio UI for VibeInvestor
Multi-agent investment research platform with real-time visualization
"""

import gradio as gr
import asyncio
from datetime import datetime
import json
import os
from typing import AsyncGenerator, Tuple, List, Dict, Any

from finder import run_finder
from memory import populate_memory, retrieve_top_k
from governor import run_governor
from verifier import verify_groundedness
from utils import generate_pdf_report, extract_json
from logger import logger
import pandas as pd

from gradio_utils import (
    format_findings_for_table,
    format_metrics_for_display,
    format_groundedness_details,
    format_iteration_trace,
    get_memory_summary,
    format_memory_for_display,
)
from main import robust_extract_findings, evaluate_run


# ============================================================================
# CORE PIPELINE LOGIC (refactored for UI integration)
# ============================================================================

class PipelineState:
    """Manages state across Gradio interface"""
    def __init__(self):
        self.current_findings: List[Dict] = []
        self.current_opportunity: str = ""
        self.current_metrics: Dict = {}
        self.current_groundedness: float = 0.0
        self.iteration_count: int = 0
        self.feedback_history: List[str] = []
        self.all_iterations_data: List[Dict] = []


async def run_pipeline_with_streaming(
    query: str, 
    max_attempts: int = 3
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Async generator that yields structured updates from the pipeline
    Each yield updates the UI with latest state
    """
    
    state = PipelineState()
    state.feedback_history = []
    
    original_query = query
    feedback = ""
    best_opportunity = None
    final_groundedness = 0
    
    for attempt in range(max_attempts):
        state.iteration_count = attempt + 1
        
        # Adapt query based on feedback
        current_query = f"{query} {feedback}".strip() if attempt > 0 else query
        
        # ========== FINDER STAGE ==========
        yield {
            "status": f"🔍 Iteration {attempt + 1}: Running Finder...",
            "tab": "discovery",
            "logs": f"[Finder] Discovering opportunities for: {current_query}",
            "iteration": f"{attempt + 1}/{max_attempts}"
        }
        
        try:
            raw_output = await run_finder(current_query)
            if isinstance(raw_output, list):
                findings = raw_output
            else:
                findings = robust_extract_findings(raw_output)
        except Exception as e:
            yield {
                "status": f"❌ Finder failed: {str(e)}",
                "error": str(e),
                "logs": f"[ERROR] Finder exception: {str(e)}"
            }
            findings = []
        
        if not findings:
            feedback = "Include related public companies even if undervaluation is borderline."
            yield {
                "status": "⚠️ No findings discovered, adapting strategy...",
                "logs": "[Adaptive] No findings. Strategy: Relaxing constraints.",
                "strategy": feedback
            }
            continue
        
        state.current_findings = findings
        
        # Format findings for UI
        findings_df = format_findings_for_table(findings)
        yield {
            "status": f"✓ Found {len(findings)} opportunities",
            "findings_table": findings_df,
            "logs": f"[Finder] Discovered {len(findings)} findings. Sample companies: {', '.join([f.get('company_name', 'N/A') for f in findings[:3]])}"
        }
        
        # ========== MEMORY UPDATE ==========
        yield {
            "status": "💾 Updating persistent memory...",
            "logs": "[Memory] Ingesting findings into FAISS vector DB..."
        }
        
        try:
            populate_memory(findings)
            yield {
                "status": "✓ Memory updated",
                "logs": "[Memory] FAISS database updated successfully"
            }
        except Exception as e:
            logger.warning(f"Memory population failed: {e}")
            yield {
                "status": f"⚠️ Memory update warning: {str(e)}",
                "logs": f"[Memory] Warning: {str(e)}"
            }
        
        # ========== MEMORY RETRIEVAL ==========
        yield {
            "status": "🧠 Consulting long-term memory...",
            "logs": "[Memory] Retrieving relevant past decisions..."
        }
        
        try:
            past_docs = retrieve_top_k(original_query, k=5)
            memory_context = "\n\n".join([d.page_content for d in past_docs]) if past_docs else ""
        except Exception as e:
            logger.warning(f"Memory retrieval failed: {e}")
            memory_context = ""
            yield {
                "status": f"⚠️ Memory retrieval warning",
                "logs": f"[Memory] Could not retrieve past context: {str(e)}"
            }
        
        # ========== GOVERNOR STAGE ==========
        yield {
            "status": f"⚖️ Governor making decision...",
            "logs": "[Governor] Analyzing findings and selecting best opportunity..."
        }
        
        try:
            best_opportunity = run_governor(findings, past_memory=memory_context)
            state.current_opportunity = best_opportunity
            
            yield {
                "status": "✓ Decision made",
                "opportunity": best_opportunity,
                "logs": f"[Governor] Selected opportunity:\n{best_opportunity[:200]}..."
            }
        except Exception as e:
            yield {
                "status": f"❌ Governor failed: {str(e)}",
                "error": str(e),
                "logs": f"[ERROR] Governor exception: {str(e)}"
            }
            best_opportunity = None
        
        # ========== VERIFIER STAGE ==========
        yield {
            "status": "🔐 Verifying groundedness...",
            "logs": "[Verifier] Cross-checking claims against evidence..."
        }
        
        try:
            v_res = verify_groundedness(best_opportunity, findings)
            final_groundedness = v_res.get("groundedness_score", 0) if isinstance(v_res, dict) else (v_res or 0)
            state.current_groundedness = final_groundedness
            
            groundedness_display = format_groundedness_details(v_res)
            
            yield {
                "status": "✓ Verification complete",
                "groundedness_details": groundedness_display,
                "logs": f"[Verifier] Groundedness Score: {final_groundedness:.1%}"
            }
        except Exception as e:
            yield {
                "status": f"⚠️ Verification warning: {str(e)}",
                "logs": f"[Verifier] Warning: {str(e)}"
            }
            final_groundedness = 0
        
        # ========== EVALUATION ==========
        yield {
            "status": "📊 Computing metrics...",
            "logs": "[Evaluation] Calculating task completion, adherence, and groundedness..."
        }
        
        try:
            metrics = evaluate_run(original_query, findings, best_opportunity, final_groundedness)
            state.current_metrics = metrics
            
            metrics_display = format_metrics_for_display(metrics)
            
            yield {
                "status": "✓ Metrics computed",
                "metrics": metrics,
                "metrics_display": metrics_display,
                "logs": f"[Evaluation] Task: {metrics['task_completion']*100:.0f}% | Adherence: {metrics['plan_adherence']*100:.0f}% | Groundedness: {metrics['groundedness']*100:.0f}%"
            }
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            metrics = {"task_completion": 0, "plan_adherence": 0, "groundedness": 0}
            yield {
                "status": f"⚠️ Evaluation failed",
                "logs": f"[ERROR] Evaluation exception: {str(e)}"
            }
        
        # ========== ADAPTIVE DECISION ==========
        if metrics["task_completion"] == 1.0 and metrics["groundedness"] >= 0.7:
            yield {
                "status": "✅ SUCCESS: Quality threshold met!",
                "logs": "[Adaptive] Success threshold reached. Pipeline complete.",
                "complete": True
            }
            break
        elif metrics["groundedness"] < 0.7:
            feedback = f"Find more primary evidence for these specific claims: {best_opportunity[:100]}"
            state.feedback_history.append("Targeted re-discovery for evidence")
            yield {
                "status": "🔄 Iterating: Low groundedness, seeking more evidence...",
                "logs": f"[Adaptive] Low groundedness ({final_groundedness:.1%}). Strategy: Targeted re-discovery.",
                "strategy": feedback
            }
        else:
            feedback = "Relax valuation heuristics to find more candidates."
            state.feedback_history.append("Broadening search constraints")
            yield {
                "status": "🔄 Iterating: Broadening search...",
                "logs": "[Adaptive] Incomplete results. Strategy: Broaden search.",
                "strategy": feedback
            }
    
    # ========== FINAL SUMMARY ==========
    yield {
        "status": "🎯 Pipeline Complete",
        "logs": "[Main] Analysis complete. Generating final summary...",
        "final_summary": {
            "iterations": state.iteration_count,
            "opportunity": state.current_opportunity,
            "metrics": state.current_metrics,
            "findings_count": len(state.current_findings),
            "memory": get_memory_summary()
        },
        "complete": True
    }

# ============================================================================
# GRADIO UI INTERFACE
# ============================================================================

def create_gradio_interface():
    """
    Creates the complete Gradio UI with 3-tab interface
    """
    
    with gr.Blocks(title="VibeInvestor") as app:
        
        gr.Markdown("# 🚀 VibeInvestor - Multi-Agent Investment Research")
        gr.Markdown("Real-time visualization of agentic discovery, analysis, and verification")
        
        # Shared state across tabs
        state_findings = gr.State([])
        state_metrics = gr.State({})
        state_opportunity = gr.State("")
        state_groundedness = gr.State(0.0)
        state_memory = gr.State({})
        
        with gr.Row():
            input_query = gr.Textbox(
                label="Investment Query",
                placeholder="e.g., Find undervalued AI companies in healthcare sector with positive cash flow",
                lines=2,
                scale=3
            )
            run_btn = gr.Button("🚀 Run Analysis", scale=1, variant="primary")
        
        iteration_display = gr.Textbox(
            label="Current Iteration",
            value="Ready to start",
            interactive=False,
            scale=1
        )
        
        with gr.Tabs():
            # ========== TAB 1: DISCOVERY ENGINE ==========
            with gr.TabItem("🔍 Discovery Engine", id="discovery"):
                gr.Markdown("### Real-time Discovery Pipeline")
                
                with gr.Row():
                    status_display = gr.Textbox(
                        label="Status",
                        value="Ready",
                        interactive=False,
                        lines=1
                    )
                    strategy_display = gr.Textbox(
                        label="Adaptive Strategy",
                        value="",
                        interactive=False,
                        lines=1
                    )
                
                logs_output = gr.Textbox(
                    label="Live Logs",
                    value="",
                    lines=20,
                    interactive=False,
                    max_lines=50
                )
                
                findings_table = gr.Dataframe(
                    label="Discovered Opportunities",
                    headers=["Company", "Ticker", "Summary", "Metrics"],
                    datatype=["str", "str", "str", "str"],
                    interactive=False,
                    wrap=True
                )
            
            # ========== TAB 2: DECISION ANALYSIS ==========
            with gr.TabItem("⚖️ Decision Analysis", id="decision"):
                gr.Markdown("### Governor's Decision & Verifier's Groundedness Check")
                
                with gr.Row():
                    opportunity_output = gr.Textbox(
                        label="Selected Opportunity",
                        value="[Waiting for analysis...]",
                        lines=12,
                        interactive=False
                    )
                
                gr.Markdown("### Verification Breakdown")
                
                groundedness_display = gr.Markdown(
                    value="[Waiting for verification...]"
                )
            
            # ========== TAB 3: METRICS & MEMORY ==========
            with gr.TabItem("📊 Metrics & Memory", id="metrics"):
                gr.Markdown("### System Performance Metrics")
                
                with gr.Row():
                    with gr.Column(scale=1):
                        metric_completion = gr.Number(
                            label="Task Completion %",
                            value=0,
                            interactive=False
                        )
                    
                    with gr.Column(scale=1):
                        metric_adherence = gr.Number(
                            label="Plan Adherence %",
                            value=0,
                            interactive=False
                        )
                    
                    with gr.Column(scale=1):
                        metric_groundedness = gr.Number(
                            label="Groundedness %",
                            value=0,
                            interactive=False
                        )
                
                iteration_trace = gr.Markdown(
                    value="[Waiting for analysis...]"
                )
                
                gr.Markdown("### Persistent Memory Status")
                
                memory_display = gr.Markdown(
                    value="[No analysis run yet...]"
                )
                
                clear_memory_btn = gr.Button(
                    "🗑️ Clear Memory",
                    scale=1
                )
        
        # ========== CONTROL FLOW LOGIC ==========
        
        async def run_analysis(query: str):
            """Main handler for running the pipeline with streaming updates"""
            
            if not query or not query.strip():
                yield (
                    "❌ Please enter an investment query",  # status_display
                    "No query provided",  # logs_output
                    pd.DataFrame(),  # findings_table
                    "",  # opportunity_output
                    "",  # groundedness_display
                    "",  # strategy_display
                    0,  # metric_completion
                    0,  # metric_adherence
                    0,  # metric_groundedness
                    "",  # iteration_trace
                    "",  # memory_display
                    ""  # iteration_display
                )
                return
            
            # Initialize displays
            logs = ""
            
            async for update in run_pipeline_with_streaming(query, max_attempts=3):
                
                # Build status message
                status_msg = update.get("status", "")
                iteration_msg = update.get("iteration", "")
                
                # Append logs
                if "logs" in update:
                    logs += update["logs"] + "\n"
                
                # Get individual values for each output
                status_display = f"{status_msg} ({iteration_msg})" if iteration_msg else status_msg
                logs_output = logs
                iteration_display = iteration_msg or ""
                
                # Get findings table
                findings_table = update.get("findings_table", pd.DataFrame())
                
                # Get opportunity
                opportunity_output = update.get("opportunity", "")
                
                # Get groundedness
                groundedness_display = update.get("groundedness_details", "")
                
                # Get strategy
                strategy_display = update.get("strategy", "")
                
                # Get metrics
                if "metrics" in update and "metrics_display" in update:
                    metrics_disp = update["metrics_display"]
                    metric_completion = metrics_disp.get("task_completion", 0)
                    metric_adherence = metrics_disp.get("plan_adherence", 0)
                    metric_groundedness = metrics_disp.get("groundedness", 0)
                    iteration_trace = format_iteration_trace(
                        update.get("final_summary", {}).get("iterations", 1),
                        []
                    )
                else:
                    metric_completion = 0
                    metric_adherence = 0
                    metric_groundedness = 0
                    iteration_trace = ""
                
                # Get memory display
                if "final_summary" in update:
                    memory_info = update["final_summary"].get("memory", {})
                    memory_display = format_memory_for_display(memory_info)
                else:
                    memory_display = ""
                
                # Yield output as tuple in correct order
                yield (
                    status_display,
                    logs_output,
                    findings_table,
                    opportunity_output,
                    groundedness_display,
                    strategy_display,
                    metric_completion,
                    metric_adherence,
                    metric_groundedness,
                    iteration_trace,
                    memory_display,
                    iteration_display
                )
        
        def clear_memory():
            """Clear FAISS memory"""
            import shutil
            try:
                if os.path.exists("faiss_investment_db"):
                    shutil.rmtree("faiss_investment_db")
                return "✓ Memory cleared successfully"
            except Exception as e:
                return f"❌ Error clearing memory: {str(e)}"
        
        # ========== EVENT HANDLERS ==========
        
        run_btn.click(
            fn=run_analysis,
            inputs=[input_query],
            outputs=[
                status_display,
                logs_output,
                findings_table,
                opportunity_output,
                groundedness_display,
                strategy_display,
                metric_completion,
                metric_adherence,
                metric_groundedness,
                iteration_trace,
                memory_display,
                iteration_display
            ]
        )
        
        clear_memory_btn.click(
            fn=clear_memory,
            outputs=[memory_display]
        )
    
    return app


if __name__ == "__main__":
    import os
    
    app = create_gradio_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        theme=gr.themes.Soft()
    )
