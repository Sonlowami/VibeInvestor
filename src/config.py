from langchain_google_genai import ChatGoogleGenerativeAI
from dataclasses import dataclass

@dataclass
class LLMConfig:
    model: str

CONFIG = {
    "finder": LLMConfig("gemini-2.0-flash"),
    "analyst": LLMConfig("gemini-2.0-flash"),
    "governor": LLMConfig("gemini-2.0-flash"),
    "reporter": LLMConfig("gemini-2.0-flash")
}

def build_llm(role):
    cfg = CONFIG[role]
    llm = ChatGoogleGenerativeAI(model=cfg.model)
    return llm