# agent/rag.py

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import os

DATA_PATH = "data/sample_docs"

def load_documents(path=DATA_PATH):
    docs = []
    for file in os.listdir(path):
        if file.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(path, file))
            docs.extend(loader.load())
    return docs

# Load docs
documents = load_documents()

# Split
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(documents)

# Embeddings
embeddings = OpenAIEmbeddings()

# Vectorstore
vectordb = Chroma.from_documents(chunks, embeddings, persist_directory="chroma_db")
vectordb.persist()

# Retriever (THIS is what graph.py imports)
retriever = vectordb.as_retriever()
