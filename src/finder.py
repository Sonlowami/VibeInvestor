from utils import extract_json
from prompts import FINDER_TASK
from langchain_openai import ChatOpenAI
import requests
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

load_dotenv()
# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

def web_search_tool(query, num_results=5):
    """Simple web search using SearchAPI.io"""
    try:
        response = requests.get(
            "https://www.searchapi.io/api/v1/search",
            params={
                "engine": "google",
                "q": query, 
                "num": num_results
            },
            headers={"Authorization": f"Bearer {os.getenv('SEARCHAPI_KEY')}"}
        )
        print("Web search response:", response.json())
        results = response.json().get("organic_results", [])
        snippets = "\n".join([r.get("snippet", "") for r in results[:num_results]])
        return snippets
    except Exception as e:
        return f"Search failed: {str(e)}"

async def run_finder(query):
    web_results = web_search_tool(query)
    print("web_results:", web_results)
    
    prompt = FINDER_TASK.format(web_snippets=web_results)
    response = llm.invoke(prompt)
    structured = extract_json(response.content)
    
    return structured
