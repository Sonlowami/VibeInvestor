import asyncio
import json
import warnings

# Suppress langchain-core Pydantic V1 compatibility warning for Python 3.14
warnings.filterwarnings("ignore", message=".*Core Pydantic V1 functionality.*")

from logger import logger
from prompts import REPORTER_TASK
from finder import run_finder
from memory import (populate_memory, init_persistent_store, write_session_memory, read_recent_sessions, prune_memory)
from orchestrator import orchestrate
from session_state import SessionState
from governor import run_governor
from utils import generate_pdf_report
from config import build_llm
from langchain.agents import create_agent
import uuid



USER_QUERY = (
    "Which discovered investment opportunity best matches the system goal "
    "of asymmetric upside with limited attention, based on available evidence?"
)

async def main():
    logger.info("Starting VibeInvestor analysis")
    init_persistent_store()

    session_id = str(uuid.uuid4())
    session_state = SessionState(session_id, USER_QUERY)
    logger.info(f"Session initialized with ID: {session_id}")
    
    previous_sessions = read_recent_sessions(limit=5)
    logger.info(f"[INFO] Injecting previous session context into planning")


    logger.info("[INFO] Running finder...")
    result = await orchestrate(USER_QUERY, previous_sessions)

    plan = result["plan"]
    findings = result["findings"]
    critique = result["critique"]

    if findings:
        session_state.selected_tickers = [f["ticker"] for f in findings]
        session_state.financials = findings
        session_state.metrics = result["metrics"]

        write_session_memory(
            session_id=session_state.session_id,
            user_query=session_state.user_query,
            selected_tickers=session_state.selected_tickers,
            financial_summary=session_state.financials,
            metrics=session_state.metrics
        )
        prune_memory()
    else:
        logger.warning("No valid opportunities returned from finder agent")

asyncio.run(main())
