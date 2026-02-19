from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import sqlite3
import json
from datetime import datetime
import os

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

DB_PATH = "faiss_investment_db"

def populate_memory(documents, metadatas):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )

    chunks = splitter.create_documents(documents, metadatas=metadatas)

    # If DB exists → load it
    if os.path.exists(DB_PATH):
        vector_db = FAISS.load_local(
            DB_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
        vector_db.add_documents(chunks)
    else:
        vector_db = FAISS.from_documents(
            documents=chunks,
            embedding=embeddings,
        )

    vector_db.save_local(DB_PATH)

    return len(chunks)



def retrieve_top_k(query, k=5):
    vector_db = FAISS.load_local(
        DB_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )

    return vector_db.similarity_search(query, k=k)

def retrieve_memory(query, k=5):
    
    if not os.path.exists(DB_PATH):
        print("[MEMORY RETRIEVE] No memory database found")
        return []
    
    vector_db = FAISS.load_local(
        DB_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )
    
    retriever = vector_db.as_retriever(search_kwargs={"k": k})
    retriever_docs = retriever.invoke(query)

    print(f"[MEMORY RETRIEVE] Retrieved {len(retriever_docs)} documents for query: '{query}'")

    return retriever_docs

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
