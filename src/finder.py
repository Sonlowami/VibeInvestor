from utils import extract_json
from prompts import FINDER_TASK
import requests
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup
import re
from logger import logger
from config import build_llm
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain.agents import create_agent
import yfinance as yf



load_dotenv()
# Initialize LLM
llm = build_llm("finder")

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

class WebSearchInput(BaseModel):
    query: str = Field(..., description="Search query string")
    num_results: int = Field(default=5, description="Number of search results to return")
    per_page_limit: int = Field(default=3000, description="Maximum characters per page")

@tool("search-web", args_schema=WebSearchInput)
def web_search_tool(query: str, num_results=5, per_page_limit=3000):
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
    
class PublicFinancialsInput(BaseModel):
    ticker: str = Field(..., description="Ticker symbol, e.g., AAPL")

@tool("get_public_financials", args_schema=PublicFinancialsInput)
def get_public_financials(ticker: str) -> dict:
    """
    Retrieves public financial data for a given ticker symbol using yfinance.
    Information retrieved includes balance sheet, cash flow, earnings history,
    insider transactions, and institutional holders.
    """
    stock = yf.Ticker(ticker)
    if stock.history(period="1d").empty:
        return {"error": f"No data found for ticker '{ticker}'"}
    bs = stock.get_balance_sheet(as_dict=True)
    cf = stock.get_cash_flow(as_dict=True)
    eh = stock.get_earnings_history(as_dict=True)
    it = stock.get_insider_transactions(as_dict=True)
    backers = stock.get_institutional_holders(as_dict=True)
    return {
        'balance_sheet': bs,
        'cash_flow': cf,
        'earnings_history': eh,
        'insider_transactions': it,
        'institutional_holders': backers
    }
    
finder_agent = create_agent(
    model=build_llm('finder'),
    tools=[web_search_tool, get_public_financials],
    system_prompt = FINDER_TASK
)

#@tool('finder-agent')
import json

llm = build_llm("finder")


def get_candidate_tickers(query):
    prompt = f"""
    Based on this investment query:

    "{query}"

    List up to 8 publicly traded U.S. stock ticker symbols 
    that might match the sector or criteria mentioned.

    Return ONLY a JSON list of ticker symbols.
    Example:
    ["AAPL", "MSFT", "GOOGL"]
    """

    response = llm.invoke(prompt)
    content = response.content.strip()

    try:
        return json.loads(content)
    except:
        return []
    

def passes_undervaluation_filters(stock):
    try:
        info = stock.info

        pe = info.get("trailingPE")
        debt_to_equity = info.get("debtToEquity")
        market_cap = info.get("marketCap")
        book_value = info.get("bookValue")

        # Basic deterministic filters
        if pe and pe < 20:
            if debt_to_equity and debt_to_equity < 100:
                return True

        return False
    except:
        return False
    

def build_company_object(ticker, stock):
    info = stock.info

    return {
        "company_name": info.get("longName", "Unknown"),
        "ticker": ticker,
        "summary": info.get("longBusinessSummary", "")[:300],
        "metrics": {
            "pe_ratio": info.get("trailingPE", "Not disclosed"),
            "market_cap": info.get("marketCap", "Not disclosed"),
            "revenue": info.get("totalRevenue", "Not disclosed")
        },
        "financials": {
            "balance_sheet": stock.balance_sheet.to_dict() if not stock.balance_sheet.empty else "Data unavailable",
            "cash_flow": stock.cashflow.to_dict() if not stock.cashflow.empty else "Data unavailable"
        }
    }


async def run_finder(query):
    print("[FINDER] Getting candidate tickers...")

    tickers = get_candidate_tickers(query)
    print("[DEBUG] Candidate tickers:", tickers)

    findings = []

    for ticker in tickers:
        stock = yf.Ticker(ticker)

        if stock.history(period="1d").empty:
            continue

        if passes_undervaluation_filters(stock):
            company_obj = build_company_object(ticker, stock)
            findings.append(company_obj)

        if len(findings) >= 5:
            break

    print("[DEBUG] Final findings count:", len(findings))

    return findings
