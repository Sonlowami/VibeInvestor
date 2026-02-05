from utils import extract_json
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

def verify_groundedness(answer, retrieved_chunks):
    evidence = "\n".join(
        [doc.page_content for doc in retrieved_chunks]
    )

    prompt = f"""
    Compare the answer below against the evidence.

    Answer:
    {answer}

    Evidence:
    {evidence}

    Return JSON:
    {{
      "supported_claims": int,
      "total_claims": int,
      "groundedness_score": float,
      "notes": string
    }}
    """

    response = llm.invoke(prompt)
    return extract_json(response.content)
