import os
import re
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import torch

# Path to your final intent document
file_path = "./intents2_embedding_ready.md"

# 1️⃣ Read file
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 2️⃣ Split by intent blocks
intent_blocks = re.split(r"\n## INTENT ", content)[1:]

documents = []

for block in intent_blocks:
    lines = block.strip().split("\n")
    
    intent_name = lines[0].strip()
    
    # Extract TAG
    tag_match = re.search(r"TAG (.+)", block)
    tag = tag_match.group(1).strip() if tag_match else intent_name
    
    # Extract PATTERNS section
    patterns_match = re.search(r"PATTERNS (.+)", block, re.DOTALL)
    patterns_text = patterns_match.group(1).strip() if patterns_match else ""
    
    documents.append(
        Document(
            page_content=patterns_text,
            metadata={"tag": tag}
        )
    )

print(f"Loaded {len(documents)} intent documents.")

# 3️⃣ Create embeddings (BGE-small)
device = "mps" if torch.backends.mps.is_available() else "cpu"

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5",
    model_kwargs={"device": device}
)

# 4️⃣ Create Chroma vector store
vector_db = Chroma.from_documents(
    documents=documents,
    embedding=embeddings,
    persist_directory="./intent_vector_db"
)

vector_db.persist()

print("✅ Intent vector store created successfully.")