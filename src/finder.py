from browser_use import Agent, ChatGoogle
from dotenv import load_dotenv
import asyncio

load_dotenv()

async def main():
    llm = ChatGoogle(model="gemini-flash-latest")
    task = "Find the starting lineup for Man city against Tottenham last week."
    agent = Agent(task=task, llm=llm)
    result = await agent.run()
    print(result[-1].result)

if __name__ == "__main__":
    asyncio.run(main())