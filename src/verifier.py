from utils import extract_json
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

def verify_groundedness(answer, findings):
    """
    Handles findings as a list of dictionaries.
    Extracts relevant text from each finding to create the evidence base.
    """
    evidence_parts = []
    
    for f in findings:
        if isinstance(f, dict):
            # Combine available fields into a text block for the LLM to read
            text = f.get("summary", "") or f.get("opportunity_summary", "")
            metrics = str(f.get("metrics", ""))
            evidence_parts.append(f"{text} | Metrics: {metrics}")
        else:
            # Fallback for string-based findings
            evidence_parts.append(str(f))

    evidence = "\n".join(evidence_parts)

    prompt = f"""
    Compare the investment selection below against the provided evidence.
    Determine if the selection is logically supported by the facts in the evidence.

    Selection to Verify:
    {answer}

    Available Evidence:
    {evidence}

    Return ONLY JSON:
    {{
      "supported_claims": int,
      "total_claims": int,
      "groundedness_score": float,
      "notes": "Brief explanation of gaps"
    }}
    """

    response = llm.invoke(prompt)
    return extract_json(response.content)