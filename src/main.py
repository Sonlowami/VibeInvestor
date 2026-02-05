import asyncio
import json
import logging
from unittest import result
from finder import run_finder
from memory import populate_memory
from governor import run_governor
from utils import generate_pdf_report
from langchain_google_genai import ChatGoogleGenerativeAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vibe_investor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    response = llm.invoke(llm_report_prompt)
    report_text_json = response.content
    logger.info("PDF report text generated")

    generate_pdf_report(report_text_json, filename="investment_report.pdf")
    logger.info("PDF report saved: investment_report.pdf")
    logger.info("Analysis complete")

asyncio.run(main())
