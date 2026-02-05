from memory import retrieve_top_k
from verifier import verify_groundedness
from prompts import GOVERNOR_TASK
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

async def run_governor(user_query):
    retrieved_chunks = retrieve_top_k(user_query, k=5)

    context = "\n\n".join(
        [doc.page_content for doc in retrieved_chunks]
    )

    prompt = GOVERNOR_TASK.format(
        question=user_query,
        context=context
    )

    response = llm.invoke(prompt)
    answer = response.content

    verification = verify_groundedness(
        answer,
        retrieved_chunks
    )

    return {
        "answer": answer,
        "verification": verification,
        "used_chunks": retrieved_chunks
    }
