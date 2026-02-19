from config import build_llm

llm = build_llm("governor")


def run_governor(findings, past_memory=""):
    """
    Governor selects the best opportunity.
    
    Now integrates long-term memory context
    """

    findings_text = "\n\n".join(
        [f"- {f['summary']}" for f in findings]
    )

    memory_section = ""
    if past_memory:
        memory_section = f"""
        Past Relevant Memory:
        {past_memory}
        """

    prompt = f"""
    You are a Senior Investment Strategist.
    Select the single best opportunity from the Current Findings.
    
    Current Findings:
    {findings_text}

    {memory_section}

    OUTPUT STRUCTURE:
    1. Opportunity Name & Ticker
    2. Executive Summary (Why this specifically?)
    3. Key Evidence (Bullet points from findings)
    4. Strategic Alignment (How it matches the user's intent)
    5. Contextual Note (Reference to past memory if applicable)
    """

    response = llm.invoke(prompt)

    return response.content
