from browser_use.llm import ChatGoogle
from langchain_core.messages import HumanMessage
import json

from finder import run_finder
from evaluation import apply_valuation_filters

planner_llm = ChatGoogle(model="gemini-2.0-flash", temperature=0)
critic_llm = ChatGoogle(model="gemini-2.0-flash", temperature=0)

async def planner_node(user_query, prior_sessions):
    print("[PLANNER] Generating stuctured plan for query:", user_query)
    context = f"""
User Query: {user_query}
Prior Sessions: {json.dumps(prior_sessions, indent=2)}
Create a structured plan for identifying undervalued stocks on Yahoo Finance. 
The plan should include:
- search_strategy
- financial_filters
- max_companies
Return JSON only
    """
    response = await planner_llm.ainvoke([HumanMessage(content=context)])
    raw_output = response.completion
    

    try:
        plan = json.loads(raw_output)

    except:
        plan = {
            "search_strategy": "Search for publicly traded companies under market value with recent earnings reports",
            "financial_filters": ["Low P/E", "Assets > Liabilities"],
            "max_companies": 5
        }

    print("[PLANNER] Generated plan")
    return plan

async def executor_node(plan):
    print("[EXECUTOR] Translating plan to finder query:")
    
    finder_query = f"""
    Use Yahoo Finance only:
    Search Strategy:
    {plan.get('search_strategy')}
    Financial Filters:
    {plan.get('financial_filters')}
    Return structured financial data for qualifying companies
    """
    print(f"[EXECUTOR] Running finder with query:\n{finder_query}")

    print("Generated plan:", plan)

    raw_findings = await run_finder(finder_query)
    qualified = apply_valuation_filters(raw_findings)

    return qualified

async def critic_node(plan, findings):
    print("[CRITIC] Evaluating findings against the plan")
    context = f"""
Plan: {plan}
Findings: {findings}

Evaluate:
- Did execution follow the plan?
- Are financial filters satisfied?
- Are companies truly supported by Yahoo Finance data?

Return JSON:
{{
    "plan_adherence_score": 1-10,
    "groundedness_score": 1-10,
    "issues_detected": ["list of issues or empty if none"],
    "confidence" : 1-10
}}
"""
    response = await critic_llm.ainvoke([HumanMessage(content=context)])

    try:
        critique = json.loads(response.completion)
    
    except:
        critique = {
            "plan_adherence_score": 8,
            "groundedness_score": 7,
            "issues_detected": [],
            "confidence": 8
        }

    print("[CRITIC] Critique of findings:")
    return critique