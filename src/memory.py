from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

DB_PATH = "faiss_investment_db"

def populate_memory(documents, metadatas):
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


def retrieve_top_k(query, k=5):
    vector_db = FAISS.load_local(
        DB_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )

    return vector_db.similarity_search(query, k=k)
