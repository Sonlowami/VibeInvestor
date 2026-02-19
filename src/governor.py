from config import build_llm

llm = build_llm("governor")


def run_governor(findings, past_memory=""):
    """
    Governor selects the best opportunity.
    
    Now integrates long-term memory context (HW3).
    """

    findings_text = "\n\n".join(
        [f"- {f['summary']}" for f in findings]
    )

    ### HW3 ADDITION ###
    memory_section = ""
    if past_memory:
        memory_section = f"""
        Past Relevant Memory:
        {past_memory}
        """

    prompt = f"""
    You are a strategic decision-making governor.

    Your task:
    Select the single best opportunity from the list.

    Current Findings:
    {findings_text}

    {memory_section}

    Consider whether past memory suggests recurring themes,
    validated patterns, or prior strong signals.

    Output only the selected opportunity summary.
    """

    response = llm.invoke(prompt)

    return response.content
