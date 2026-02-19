from roles import planner_node, executor_node, critic_node
from evaluation import compute_metrics

async def orchestrate(user_query, prior_sessions):

    plan = await planner_node(user_query, prior_sessions) # PLAN

    findings = await executor_node(plan) # EXECUTE

    critique = await critic_node(plan, findings) # CRITIQUE

    metrics = compute_metrics(plan, findings, critique) # EVALUATE

    print("[ORCHESTRATOR] Orchestration complete. Returning results.")

    return {
        "plan": plan,
        "findings": findings,
        "critique": critique,
        "metrics": metrics
    }