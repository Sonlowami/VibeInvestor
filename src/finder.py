from utils import extract_json
from prompts import FINDER_TASK
from langchain_openai import ChatOpenAI
import requests
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup
import re
from logger import logger



load_dotenv()
# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

def _clean_text(s: str) -> str:
    s = re.sub(r'\s+', ' ', s or '').strip()
    return s

def scrape_page_text(url, timeout=8):
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "vibe-investor-bot/1.0 (+https://example.org)"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "lxml")
        # remove scripts/styles
        for tag in soup(["script", "style", "noscript", "header", "footer", "meta", "iframe"]):
            tag.decompose()
        # prefer <article> or <main>
        main = soup.find("article") or soup.find("main")
        if main:
            text = main.get_text(separator="\n")
        else:
            body = soup.find("body")
            text = body.get_text(separator="\n") if body else soup.get_text(separator="\n")
        return _clean_text(text)
    except Exception:
        return ""

def web_search_tool(query, num_results=5, per_page_limit=3000):
    """Search via SearchAPI.io, then scrape the top result pages and return formatted text."""
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
        data = response.json()
        results = data.get("organic_results", []) or []
        pages = []
        for r in results[:num_results]:
            # try common url keys
            url = r.get("link") or r.get("url") or r.get("displayed_url") or r.get("source")
            title = r.get("title") or r.get("name") or ""
            snippet = r.get("snippet", "")
            if not url:
                # fallback to snippet-only if no url found
                pages.append(f"Title: {title}\nURL: (none)\nSnippet: {snippet}\n")
                continue
            page_text = scrape_page_text(url)
            if not page_text:
                # fallback to snippet
                page_text = snippet
            # truncate to keep prompts bounded
            if len(page_text) > per_page_limit:
                page_text = page_text[:per_page_limit] + "...[truncated]"
            pages.append(f"Title: {title}\nURL: {url}\nContent:\n{page_text}\n")
        # join pages with separators
        logger.info(f"Web search returned {len(pages)} pages")
        logger.info(f"Searched pages: {[p.splitlines()[1] for p in pages]}")
        return "\n---\n".join(pages)
    except Exception as e:
        return f"Search failed: {str(e)}"

async def run_finder(query):
    web_results = web_search_tool(query)
    
    prompt = FINDER_TASK.format(web_snippets=web_results)
    response = llm.invoke(prompt)
    structured = extract_json(response.content)
    
    return structured
