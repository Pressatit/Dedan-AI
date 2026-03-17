import os
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from sklearn.metrics.pairwise import cosine_similarity

# === 1. Basic embedding setup ===
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

# === 2. Vector DB path setup ===
VECTOR_STORE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../vector_db/dekai_vector_db_new")
)

# === 3. Load the Chroma DB ===
chroma_db = Chroma(
    persist_directory=VECTOR_STORE_PATH,
    embedding_function=embedding_model
)

# === 4. Routing reference examples ===
dekut_examples = [
    "Who is the Vice Chancellor of Dedan Kimathi University?",
    "What courses are offered in Mechatronics?",
    "How can I log into the student portal?",
    "Where is DKUT located?",
    "What is the Siemens program?",
    "What are the admission requirements at DKUT?",
    "How do I register for units?",
    "What is DeSTaC?",
    "Does DKUT offer scholarships?",
    "Who is the Dean of School of Engineering?",
    "What are the programmes offered in the Institute of Tourism and Hospitality Management?",
    "What is the meaning of IGGReS and ICFoSS in full?"
]

example_vectors = [embedding_model.embed_query(q) for q in dekut_examples]

def is_dekut_question(user_query: str, threshold: float = 0.75) -> bool:
    user_vec = embedding_model.embed_query(user_query)
    sims = cosine_similarity([user_vec], example_vectors)[0]
    return max(sims) >= threshold

#results = chroma_db.similarity_search("School of Engineering building DeKUT", k=5)

#for r in results:
    print("-----")
    print(r.page_content[:400])