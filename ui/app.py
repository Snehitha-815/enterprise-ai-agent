# ui/app.py

import streamlit as st
import httpx
import json
import os
BACKEND_URL = os.getenv("BACKEND_URL")
if BACKEND_URL is None: 
    st.error("BACKEND_URL is not set in environment variables.")
st.set_page_config(page_title="Enterprise AI Agent", layout="wide")

st.title("💼 Enterprise AI Agent")
st.write("Ask questions based on your documents.")

# Chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Display chat history
for msg in st.session_state["messages"]:
    st.chat_message(msg["role"]).write(msg["content"])

# User input
user_input = st.chat_input("Ask something about your documents...")

if user_input:
    # Add user message
    st.session_state["messages"].append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    # Placeholder for streaming assistant message
    message_placeholder = st.chat_message("assistant").empty()
    full_answer = ""
    context_data = None

    # Stream from backend using httpx
    with httpx.stream(
        "POST",
        f"{BACKEND_URL}/ask",
        json={"question": user_input},
        timeout=None
    ) as response:


        for raw_line in response.iter_lines():
            if not raw_line:
                continue
            # Handle both bytes and strings 
            if isinstance(raw_line, bytes): 
                line = raw_line.decode("utf-8").strip() 
            else: 
                line = raw_line.strip()
            
            if not line:
                continue
            # Skip SSE prefixes if they appear 
            if line.startswith("data:"): 
                line = line[5:].strip() 
                if not line: 
                    continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError: 
                # Skip anything that is not valid JSON 
                continue

            # Stream chunks
            if "chunk" in data:
                full_answer += data["chunk"]
                message_placeholder.write(full_answer)

            # Final answer + context
            if "final_answer" in data:
                full_answer = data["final_answer"]
                message_placeholder.write(full_answer)
                context_data = data.get("context", [])

    # Save final answer to history
    st.session_state["messages"].append({"role": "assistant", "content": full_answer})

    # Show retrieved context
    if context_data:
        with st.expander("🔍 Retrieved Context"):
            for c in context_data:
                source = c.get("source", "unknown") 
                page = c.get("page", "N/A") 
                st.write(f"**Source:** {source} — **Page:** {page}")
                st.write(c["text"])
                st.write("---")