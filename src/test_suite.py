import asyncio
import pandas as pd
from main import main as run_pipeline
import os
import shutil

# Define the Test Cases
TEST_CASES = [
    {"id": 1, "name": "Baseline", "query": "Undervalued semiconductor stocks with recent product launches"},
    {"id": 2, "name": "Specificity", "query": "Healthcare companies using generative AI for drug discovery with a P/E ratio below 20"},
    {"id": 3, "name": "Memory", "query": "Based on our previous research into semiconductors, find a competitor with a similar storage focus"},
    {"id": 4, "name": "Adaptive", "query": "Publicly traded deep-sea mining companies with validated revenue"},
    {"id": 5, "name": "Failure", "query": "Undervalued stocks in the teleportation industry"}
]

async def start_automated_evaluation():
    # Setup: Clear old memory to ensure a fresh baseline for Case 1
    if os.path.exists("faiss_investment_db"):
        shutil.rmtree("faiss_investment_db")
        print("[SETUP] Cleared old FAISS memory for clean baseline.")

    all_results = []
    
    print(f" Starting Evaluation... {len(TEST_CASES)} cases.\n")

    for case in TEST_CASES:
        print(f"--- Running Case {case['id']}: {case['name']} ---")
        try:
            # Run the actual agentic pipeline
            metrics = await run_pipeline(case['query'])
            
            # Combine case info with actual performance metrics
            record = {**case, **metrics}
            all_results.append(record)
            print(f"Success: Groundedness {metrics['groundedness']} | Attempts {metrics['attempts']}")
        
        except Exception as e:
            print(f"Critical Failure in {case['name']}: {e}")
            all_results.append({**case, "status": "FAILED", "error": str(e)})

    # Export to CSV for the Report
    df = pd.DataFrame(all_results)
    df.to_csv("HW3_Evaluation_Results.csv", index=False)
    
    print("\n" + "="*30)
    print("📊 EVALUATION COMPLETE")
    print("Summary Table:")
    print(df[['name', 'attempts', 'plan_adherence', 'groundedness']])
    print("="*30)
    print("File saved: HW3_Evaluation_Results.csv")

if __name__ == "__main__":
    asyncio.run(start_automated_evaluation())