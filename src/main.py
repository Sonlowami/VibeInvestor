import asyncio
import json
from logger import logger
from prompts import REPORTER_TASK
from finder import run_finder
from memory import populate_memory
from governor import run_governor
from utils import generate_pdf_report
from config import build_llm
from langchain.agents import create_agent


USER_QUERY = (
    "Which discovered investment opportunity best matches the system goal "
    "of asymmetric upside with limited attention, based on available evidence?"
)

async def main():
    logger.info("Starting VibeInvestor analysis")
    
    logger.info("Running finder...")
    findings = await run_finder(
        "Publicly traded companies under market value with recent earnings reports"
    )
    logger.info(f"Finder returned type: {type(findings)}")
    logger.info(f"Finder raw output: {findings}")

    if isinstance(findings, dict):
        if "error" in findings:
            logger.error(f"Finder error: {findings['error']}")
            return
        else:
            findings = [findings]
            logger.info("Wrapped single finding into list")

    elif not isinstance(findings, list):
        logger.error(f"Unexpected type from finder: {type(findings)}")
        return

    logger.info(f"Found {len(findings)} findings")
    
    if len(findings) == 0:
        logger.warning("No findings returned")
        return

    logger.info("Populating memory with findings...")
    documents, metadatas = [], []
    for i, f in enumerate(findings):
        documents.append(f["summary"])
        metadatas.append({"source": f["source"]})
    
    populate_memory(documents, metadatas)
    logger.info(f"Memory populated with {len(documents)} documents")

    logger.info("Running governor...")
    result = await run_governor("Which opportunity has strong asymmetric upside?")
    logger.info("Governor analysis complete")

    report_text = {
        "answer": result["answer"],
        "verification": result["verification"],
        "used_chunks": [doc.page_content for doc in result["used_chunks"]]
    }

    report_text_json = json.dumps(report_text, indent=2)
    logger.info("Report compiled")

    logger.info("Generating PDF report via LLM...")
    llm_report_prompt = f"""
    Based on the following JSON report, generate a concise and clear investment report
    suitable for presentation to stakeholders. Summarize the key findings, verification
    results, and evidence used.
    JSON Report:
    {report_text_json}
    """
    reporter_agent = create_agent(
        model=build_llm('governor'),
        tools=[generate_pdf_report],
        system_prompt=REPORTER_TASK
    )
    report_text_json = reporter_agent.invoke({
        "messages": [{"role": 'user', 'content': llm_report_prompt}]
    })
    logger.info("PDF report text generated")
    logger.info("PDF report saved: investment_report.pdf")
    logger.info("Analysis complete")

asyncio.run(main())
