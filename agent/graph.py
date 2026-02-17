# agent/graph.py

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from agent.rag import retriever, vectordb
from typing import List, Any

class AgentState(dict):
    question: str
    docs: List[Any]
    answer: str

def retrieve_node(state: AgentState):
    question = state["question"]
    docs_with_scores = vectordb.similarity_search_with_score(question, k=5)
    docs = [doc for doc, score in docs_with_scores if score > 0.2]

    return {"docs": docs}

def llm_node(state: AgentState):
    llm = ChatOpenAI(model="gpt-4o-mini")  # NOT streaming here
    question = state["question"]
    docs = state["docs"]

    context_text = "\n\n".join([d.page_content[:500] for d in docs])

    prompt = f"""
Use ONLY the context below to answer the question.

Context:
{context_text}

Question: {question}
"""

    answer = llm.invoke(prompt).content
    return {"answer": answer}

def build_agent():
    workflow = StateGraph(AgentState)

    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("llm", llm_node)

    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "llm")
    workflow.add_edge("llm", END)

    return workflow.compile()
