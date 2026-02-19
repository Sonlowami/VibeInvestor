from finder import run_finder
from memory import populate_memory, retrieve_memory
from governor import run_governor
from verifier import verify_groundedness
from utils import generate_pdf_report
import asyncio
import json


def normalize_findings(raw_findings):
    if raw_findings is None:
        return []

    if isinstance(raw_findings, str):
        try:
            raw_findings = json.loads(raw_findings)
        except Exception:
            return []

    if isinstance(raw_findings, dict):
        raw_findings = [raw_findings]

    if not isinstance(raw_findings, list):
        return []

    return [item for item in raw_findings if isinstance(item, dict)]


### HW3 ADDITION ###
def evaluate_run(query, findings, selected_opportunity, groundedness_score):
    """
    Quantitative Evaluation Metrics (HW3)

    Metrics:
    1. Task Completion
    2. Plan Adherence
    3. Groundedness
    """

    # Metric 1 — Task Completion
    task_completion = 1 if findings and selected_opportunity else 0

    # Metric 2 — Plan Adherence
    adherence_score = 0
    if selected_opportunity:
        query_keywords = query.lower().split()
        match_count = sum(
            1 for word in query_keywords
            if word in selected_opportunity.lower()
        )
        adherence_score = match_count / max(len(query_keywords), 1)

    # Metric 3 — Groundedness (already computed by verifier)
    groundedness = groundedness_score

    evaluation = {
        "task_completion": task_completion,
        "plan_adherence_score": round(adherence_score, 2),
        "groundedness_score": groundedness
    }

    print("\n[EVALUATION OUTPUT]")
    print(evaluation)

    return evaluation


async def main(query):

    ### HW3 ADDITION ###
    # Adaptive control parameters
    max_attempts = 2
    attempt = 0

    best_opportunity = None
    groundedness_score = 0

    while attempt < max_attempts:

        print(f"\n[MAIN] Attempt {attempt + 1}")

        # 1. Finder
        print("[MAIN] Running finder...")
        raw_findings = await run_finder(query)
        findings = normalize_findings(raw_findings)

        if not findings:
            print("[MAIN] No findings returned.")

        # 2. Memory Write (Long-Term)
        print("[MAIN] Populating memory...")
        documents = [f["summary"] for f in findings] if findings else []
        metadatas = [{"source": f.get("source", "unknown")} for f in findings] if findings else []

        if documents:
            populate_memory(documents, metadatas)

        # 3. Memory Read (Long-Term Reuse)
        print("[MAIN] Retrieving relevant past memory...")
        past_memory_docs = retrieve_memory(query)

        past_memory_text = ""
        if past_memory_docs:
            past_memory_text = "\n\n".join(
                [doc.page_content for doc in past_memory_docs]
            )

        # 4. Governor (Decision Node)
        print("[MAIN] Running governor...")
        best_opportunity = run_governor(
            findings,
            past_memory=past_memory_text
        )

        # 5. Groundedness Verification
        print("[MAIN] Verifying groundedness...")
        groundedness_result = verify_groundedness(best_opportunity, past_memory_docs)
        if isinstance(groundedness_result, dict):
            groundedness_score = groundedness_result.get("groundedness_score", 0)
        else:
            groundedness_score = groundedness_result or 0

        # 6. Evaluation Metrics
        evaluation_metrics = evaluate_run(
            query,
            findings,
            best_opportunity,
            groundedness_score
        )

        ### HW3 ADDITION — ADAPTIVE DECISION ###
        if (
            evaluation_metrics["task_completion"] == 1
            and evaluation_metrics["groundedness_score"] >= 0.5
        ):
            print("[ADAPTIVE] Acceptable result achieved.")
            break

        print("[ADAPTIVE] Performance insufficient. Relaxing query...")

        # Modify query slightly for retry
        query = query + " broader related signals"

        attempt += 1

    # 7. Reporting
    print("[MAIN] Generating report...")
    report_text = (
        f"Query: {query}\n\n"
        f"Selected Opportunity:\n{best_opportunity}\n\n"
        f"Groundedness Score: {groundedness_score}"
    )
    generate_pdf_report.invoke(
        {"text": report_text, "filename": "investment_report.pdf"}
    )

    print("[MAIN] Done.")


if __name__ == "__main__":
    user_query = input("Enter your query: ")
    asyncio.run(main(user_query))
