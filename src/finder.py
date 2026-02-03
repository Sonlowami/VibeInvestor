from browser_use import Agent, ChatGoogle
from browser_use.llm import ChatDeepSeek
from dotenv import load_dotenv
import asyncio
from prompts import FinderPrompt

load_dotenv()

deep_seek_llm = ChatDeepSeek(base_url="https://api.deepseek.com", model="deepseek-chat")

gemini_llm = ChatGoogle(model="gemini-2.0-flash", temperature=0.7)

async def main():
    llm = gemini_llm
    task = FinderPrompt
    agent = Agent(task=task, llm=llm)
    result = await agent.run()
    print(result)

if __name__ == "__main__":
    asyncio.run(main())