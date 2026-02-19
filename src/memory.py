from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.tools import tool
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from typing import List
import os
from logger import logger

load_dotenv()

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

DB_PATH = "faiss_investment_db"

def extract_text_from_findings(findings):
    documents, metadatas = [], []
    for f in findings:
        texts = [
            f"summary: {f['summary']}",
            f"financials: {f['financials']}",
            f"metrics: {f['metrics']}",
            f"company_name: {f['company_name']}",
            f"ticker: {f['ticker']}"
        ]
        texts = " \n".join(texts)
        documents.append(texts)
        metadatas.extend([{"source": f["source"]}] * len(texts.split('\n')))
    return documents, metadatas

def populate_memory(findings):
    """
    
    Each dict must have: company_name, ticker, summary, financials, metrics, source
    """
    logger.info(f"Populating memory with {len(findings)} findings...")
    
    documents, metadatas = extract_text_from_findings(findings)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )

    chunks = splitter.create_documents(documents, metadatas=metadatas)

    vector_db = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings,
    )
    vector_db.save_local(DB_PATH)

    return len(chunks)


class RetrieveTopKInput(BaseModel):
    query: str = Field(..., description="Query string to search for")
    k: int = Field(5, description="Number of top results to retrieve")
    
#@tool("retrieve-top-k", args_schema=RetrieveTopKInput)
def retrieve_top_k(query, k=5):
    vector_db = FAISS.load_local(
        DB_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )
    results = vector_db.similarity_search(query, k=k)
    print(f"Retrieved {len(results)} results for query: {query}")
    print(f"Top results: {[r for r in results]}")
    return results

def prune_memory(max_entries=200):
    if not os.path.exists(DB_PATH):
        print("[MEMORY PRUNE] No memory database found")
        return
    
    vector_db = FAISS.load_local(
        DB_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )

    if len(vector_db.docstore._dict) <= max_entries:
        return
    
    print(f"[MEMORY PRUNE] Pruning memory...")

    all_docs = list(vector_db.docstore._dict.values())
    trimmed_docs = all_docs[-max_entries:]

    vector_db = FAISS.from_documents(trimmed_docs, embeddings)
    vector_db.save_local(DB_PATH)
