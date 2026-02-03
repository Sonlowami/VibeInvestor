import json
from browser_use import Agent

async def main():
    agent = Agent(task="Find the price of Bitcoin on CoinMarketCap", llm=llm)
    history = await agent.run()
    
    # The last history item contains the final result
    final_result = history[-1].result
    
    print("--- FINAL AGENT RESPONSE ---")
    print(final_result)
