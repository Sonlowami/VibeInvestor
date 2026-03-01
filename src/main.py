from finder import run_finder
from memory import populate_memory, retrieve_top_k
from governor import run_governor
from verifier import verify_groundedness
from utils import generate_pdf_report, extract_json
import asyncio
import json
import re
from logger import logger
import pandas as pd
from datetime import datetime

def robust_extract_findings(raw_text: str):
    """
    Robust extraction to handle semi-structured Gemini outputs.
    Ensures discovery doesn't fail due to conversational preambles
    """
    if not raw_text or not str(raw_text).strip():
        return []

    #Try to find JSON in markdown blocks
    json_match = re.search(r"```json\s*([\s\S]*?)\s*```", raw_text)
    content_to_parse = json_match.group(1) if json_match else raw_text

    #Strict JSON parsing
    try:
        clean_content = re.sub(r",\s*([\]}])", r"\1", content_to_parse.strip())
        data = json.loads(clean_content)
        if isinstance(data, list): return data
        if isinstance(data, dict): return [data]
    except Exception:
        logger.warning("Strict JSON parsing failed. Attempting regex extraction.")

    #Fallback: Regex-based object extraction
    try:
        items = re.findall(r"\{[^{}]*\"company_name\"[^{}]*\}", raw_text, re.DOTALL)
        parsed_items = []
        for item in items:
            try:
                parsed_items.append(json.loads(item))
            except: continue
        if parsed_items: return parsed_items
    except Exception:
        pass

    return []

def evaluate_run(query, findings, selected_opportunity, groundedness_score):
    """
    Quantitative Evaluation Metrics
    Uses a small LLM call for semantic Plan Adherence.
    """
    # Metric 1: Task Completion (Binary)
    task_completion = 1.0 if (findings and selected_opportunity) else 0.0

    # Metric 2: Semantic Plan Adherence (LLM Call)
    adherence_score = 0.0
    if selected_opportunity:
        adherence_prompt = f"""
        Rate how well the Selected Opportunity matches the user's Original Query.
        
        Original Query: {query}
        Selected Opportunity: {selected_opportunity}
        
        Return ONLY a JSON object:
        {{
          "score": float (0.0 to 1.0),
          "reason": "short explanation"
        }}
        """
        try:
            # Reusing build_llm from your config to keep it consistent
            from config import build_llm
            eval_llm = build_llm("governor") 
            resp = eval_llm.invoke(adherence_prompt)
            from utils import extract_json

            adherence_data = extract_json(resp.content)
            adherence_score = float(adherence_data.get("score", 0.0))
        except Exception as e:
            print(f"Adherence Eval Error: {e}")
            adherence_score = 0.0

    # Metric 3: Groundedness
    groundedness = float(groundedness_score)

    evaluation = {
        "task_completion": task_completion,
        "plan_adherence": adherence_score,
        "groundedness": groundedness
    }
    
    print(f"\n[EVALUATION] {evaluation}")
    return evaluation

async def main(query):
    
    max_attempts = 3
    attempt = 0
    feedback = ""
    
    best_opportunity = None
    final_groundedness = 0
    original_query = query

    while attempt < max_attempts:
        print(f"\n--- [MAIN] Iteration {attempt + 1} ---")
        
        # Adapt the query based on previous attempt feedback
        current_query = f"{query} {feedback}".strip() if attempt > 0 else query

        # Finder (Discovery)
        print("[MAIN] Running Finder...")
        raw_output = await run_finder(current_query)

        if isinstance(raw_output, list):
            findings = raw_output
        else:
            findings = robust_extract_findings(raw_output)

        if not findings:
            print("[ADAPTIVE] Failure: No findings. Strategy: Relaxing constraints.")
            feedback = "Include related public companies even if undervaluation is borderline."
            attempt += 1
            continue

        #Persistent Memory Write
        print("[MAIN] Updating Persistent Memory (FAISS)...")
        populate_memory(findings)

        #Memory Read (Contextual Influencing)
        print("[MAIN] Consulting long-term memory...")
        past_docs = retrieve_top_k(original_query)
        memory_context = "\n\n".join([d.page_content for d in past_docs]) if past_docs else ""

        # Governor (Decision)
        print("[MAIN] Running Governor...")
        best_opportunity = run_governor(findings, past_memory=memory_context)

        #Verifier (Grounding)
        print("[MAIN] Verifying Groundedness...")
        v_res = verify_groundedness(best_opportunity, findings)
        final_groundedness = v_res.get("groundedness_score", 0) if isinstance(v_res, dict) else (v_res or 0)

        #Evaluation
        metrics = evaluate_run(original_query, findings, best_opportunity, final_groundedness)

        #Adaptive Decision Bridge
        if metrics["task_completion"] == 1.0 and metrics["groundedness"] >= 0.7:
            print("[ADAPTIVE] Success threshold met.")
            break
        elif metrics["groundedness"] < 0.7:
            print("[ADAPTIVE] Low groundedness. Strategy: Targeted re-discovery.")
            feedback = f"Find more primary evidence for these specific claims: {best_opportunity[:100]}"
        else:
            print("[ADAPTIVE] Incomplete results. Strategy: Broaden search.")
            feedback = "Relax valuation heuristics to find more candidates."
            
        attempt += 1

    #Final Reporting
    print("\n[MAIN] Generating Comprehensive PDF Report...")
    
    report_text = f"""
    INVESTMENT RESEARCH INTELLIGENCE REPORT
    ========================================
    Target Query: {original_query}
    Session ID: {pd.Timestamp.now().strftime('%Y%m%d-%H%M')}
    
    1. EXECUTIVE DECISION
    ---------------------
    {best_opportunity}
    
    2. SYSTEM PERFORMANCE & EVALUATION
    ----------------------------------
    - Task Completion: {metrics['task_completion'] * 100}%
    - Plan Adherence:  {metrics['plan_adherence'] * 100}%
    - Groundedness:    {metrics['groundedness'] * 100}%
    
    3. ADAPTIVE EXECUTION TRACE
    ---------------------------
    - Total Iterations: {attempt + 1}
    - Final Strategy: {"Success on first pass" if attempt == 0 else "Adaptive refinement applied"}
    - Memory Context: {"Integrated" if past_docs else "New discovery"}
    
    4. DATA SOURCE INTEGRITY
    ------------------------
    This report was generated by a multi-agent orchestration (Finder -> Governor -> Verifier)
    and cross-referenced against FAISS persistent long-term memory.
    """
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"reports/HW3_Final_Investment_Report_{timestamp}.pdf"
    generate_pdf_report.invoke({"text": report_text, "filename": filename})
    print("[MAIN] Pipeline Complete.")

    return {
        "query": original_query,
        "attempts": attempt + 1,
        "task_completion": metrics["task_completion"],
        "plan_adherence": metrics["plan_adherence"],
        "groundedness": metrics["groundedness"],
        "result": best_opportunity[:100] + "..."
    }

if __name__ == "__main__":
    user_query = input("Enter investment query: ")
    asyncio.run(main(user_query))
