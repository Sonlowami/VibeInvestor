from memory import retrieve_top_k
from verifier import verify_groundedness
from prompts import GOVERNOR_TASK
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from config import build_llm

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

async def run_governor(user_query):
    retrieved_chunks = retrieve_top_k(user_query, k=5)

    context = "\n\n".join(
        [doc.page_content for doc in retrieved_chunks]
    )

    prompt = GOVERNOR_TASK.format(
        context=context
    )
    governor_agent = create_agent(
        model=build_llm('governor'),
        system_prompt=prompt
    )
    result = governor_agent.invoke({
        'messages': [{'role': 'user', 'content': user_query}]
    })
    answer = result['messages'][-1].content

    verification = verify_groundedness(
        answer,
        retrieved_chunks
    )

    return {
        "answer": answer,
        "verification": verification,
        "used_chunks": retrieved_chunks
    }
