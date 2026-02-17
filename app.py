from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.responses import StreamingResponse
import json

load_dotenv()

from agent.graph import build_agent
from langchain_openai import ChatOpenAI

app = FastAPI()
agent = build_agent()

class Query(BaseModel):
    question: str

@app.post("/ask")
def ask_agent(query: Query):

    # Run graph normally (no streaming)
    result = agent.invoke({"question": query.question})

    docs = result["docs"]
    final_answer = result["answer"]

    # Now stream ONLY the LLM answer
    llm = ChatOpenAI(model="gpt-4o-mini", streaming=True)

    def stream_answer():
        for chunk in llm.stream(final_answer):
            yield json.dumps({"chunk": chunk.content}) + "\n"

        # After streaming, send context
        context = [
            {
                "text": d.page_content[:300], 
                "source": d.metadata.get("source", "unknown"), 
                "page": d.metadata.get("page", d.metadata.get("page_number", "N/A"))
            }
            for d in docs
        ]

        yield json.dumps({
            "final_answer": final_answer,
            "context": context
        }) + "\n"

    return StreamingResponse(stream_answer(), media_type="text/event-stream")
