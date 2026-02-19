import asyncio
from orchestrator import orchestrate
from memory import read_recent_sessions

TEST_CASES = [

    "Find undervalued tech stocks on Yahoo Finance",
    # " Find undervalued healthcare stocks on Yahoo Finance",
    # "Find undervalued energy stocks on Yahoo Finance",
    # "Find undervalued small cap stocks on Yahoo Finance",
    # "Find undervalued dividend stocks on Yahoo Finance",
    # "Find undervalued companies with strong cash flow on Yahoo Finance",
]

async def run_tests():
    results = []
    for query in TEST_CASES:
        print(f"\nRunning test case: {query}")
        prior = read_recent_sessions(limit=3)

        result = await orchestrate(query, prior)

        results.append({
            "query": query,
            "metrics": result["metrics"]
        })
    return results

def print_results_table(results):
    
    print("\nTest Results:")
    for res in results:
        print(
            f"Query:{res['query']}\n"
            f"Plan Adherence: {res['metrics']['plan_adherence_score']}\n"
            f"Groundedness: {res['metrics']['groundedness_score']}\n"
            f"Task Completed: {res['metrics']['task_completion']}\n"
        )

async def main():
    results = await run_tests()
    print_results_table(results)


if __name__ == "__main__":
    asyncio.run(main())