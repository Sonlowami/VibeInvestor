import json
import re
from fpdf import FPDF
from langchain.tools import tool
from pydantic import BaseModel, Field

def extract_json(raw_text):
    """Extract and parse JSON from LLM response with robust error handling"""
    # First, try parsing the raw text directly
    try:
        return json.loads(raw_text)
    except Exception:
        pass

    # Try to find JSON array or object in the text
    # Look for array first (since we expect array of findings)
    array_match = re.search(r'\[.*\]', raw_text, re.DOTALL)
    if array_match:
        try:
            return json.loads(array_match.group())
        except json.JSONDecodeError as e:
            print(f"JSON parse error for array: {e}")
            print(f"Attempted to parse: {array_match.group()[:200]}...")
    
    # Try object
    object_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
    if object_match:
        try:
            return json.loads(object_match.group())
        except json.JSONDecodeError as e:
            print(f"JSON parse error for object: {e}")
            print(f"Attempted to parse: {object_match.group()[:200]}...")

    # If all parsing fails, return the raw text for debugging
    print(f"WARNING: Could not extract valid JSON from response")
    print(f"Raw response: {raw_text[:500]}...")
    return {"error": "Failed to parse JSON", "raw_response": raw_text}

class GeneratePdfReportInput(BaseModel):
    text: str = Field(..., description="Text content for the PDF")
    filename: str = Field(..., description="Filename of the output pdf")


@tool('generate-report', args_schema=GeneratePdfReportInput)
def generate_pdf_report(text, filename="report.pdf"):
    """
    Writes the given text to a PDF file with the specified filename.
    
    :param text: Description
    :param filename: Description
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for line in text.split("\n"):
        pdf.multi_cell(0, 8, line)

    pdf.output(filename)
