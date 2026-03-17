from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import torch
import responses_conv

# 1️⃣ Setup embedding model (must match creation)
device = "mps" if torch.backends.mps.is_available() else "cpu"

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5",
    model_kwargs={"device": device}
)

# 2️⃣ Load persisted vector DB
vector_db = Chroma(
    persist_directory="./intent_vector_db",
    embedding_function=embeddings
)

def get_intent(query, threshold=0.6):
    
    formatted_query = f"Represent this sentence for retrieval: {query}"
    
    results = vector_db.similarity_search_with_score(
        formatted_query,
        k=1
    )
    
    if not results:
        return "fallback", None
    
    best_doc, distance = results[0]
    
    # LOWER distance = better match
    if distance <= threshold:
        return best_doc.metadata["tag"], distance
    else:
        return "fallback", distance
    
while True:
  user_input = input("You: ")
    
  tag, confidence = get_intent(user_input)
    
  print("Matched Intent:", tag)
  print("Confidence:", round(confidence, 3))

  engine = responses_conv.IntentEngine()
  response = engine.get_response(tag)
  print(f"Response is : {response}" )
