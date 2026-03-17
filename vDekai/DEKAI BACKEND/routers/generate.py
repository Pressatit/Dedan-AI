from fastapi import APIRouter, Depends,requests,HTTPException
from sqlalchemy.orm import Session
from schemas import Message
from oath2 import get_current_user
import schemas
import models
from database import sessionmk
from vector_store import chroma_db, is_dekut_question
from langchain_core.documents import Document  
import logging
import re

#models
from model import dekainlp01,openrouter,dekainlp15

logger = logging.getLogger(__name__)


router = APIRouter(
    tags=["generation"]
)


def get_db():
    db=sessionmk()
    try:
        yield db
    finally:
        db.close()
"""
def serialize_history(db_messages):
    formatted = []

    for m in db_messages:
        role = "assistant" if m.sender == "assistant" else "user"
        formatted.append({
            "role": role,
            "content": m.content
        })

    return formatted
"""
def serialize_history(db_messages):
    formatted = []
    for m in db_messages:
        # 1. Ensure we only send 'user' or 'assistant' roles
        # 2. Ensure content is a string and not empty
        role = "assistant" if getattr(m, 'sender', None) == "assistant" else "user"
        content = getattr(m, 'content', "")
        
        if content and content.strip():
            formatted.append({"role": role, "content": content.strip()})
    
    return formatted
"""
def clean_markdown(text: str) -> str:
    #Remove markdown formatting (asterisks, bold, italic, links) from text.
    # Remove bold (**text** or __text__)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    # Remove italic (*text* or _text_)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    # Remove remaining standalone asterisks
    text = text.replace('*', '')
    # Remove markdown links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    return text.strip()
"""

@router.post("/conversation/{conversation_id}/generate")
def generate_reply(
    conversation_id: int,
    request: schemas.GenerateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # 1️⃣ Verify conversation ownership
    conversation = db.query(models.Conversation).filter(
        models.Conversation.conversation_id == conversation_id,
        models.Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # 2️⃣ Fetch last N messages
    messages = (
        db.query(models.Message)
        .filter(models.Message.conversation_id == conversation_id)
        .order_by(models.Message.created_at.asc())
        .limit(6)
        .all()
    )
    messages = list(reversed(messages))

    # 3️⃣ Build history
    history = []
    for m in messages:
        history.append(m.content)

    # 4️⃣ Generate
    reply = dekainlp01.generate_reply_from_history(history)

    if not reply:
     reply = "🙂 Tell me a bit more."

    # Clean markdown formatting from output
    

    return {"text": reply}




@router.post("/conversation/{conversation_id}/generater")
def generate_open_reply(
    conversation_id: int,
    request_data: schemas.GenerateRequest, # <--- THIS IS REQUIRED to process the POST body
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    
    # 1. Verify ownership (standard check)
    conversation = db.query(models.Conversation).filter(
        models.Conversation.conversation_id == conversation_id,
        models.Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # 1. Fetch messages from DB
   
    db_messages = (
        db.query(models.Message)
        .filter(models.Message.conversation_id == conversation_id)
        .order_by(models.Message.created_at)
        .all()
    )

    query = request_data.prompt
    """
    # --- 0. Query expansion: Handle common abbreviations and variations ---
    def expand_query(q: str) -> str:
        Expand abbreviations and common variations for better retrieval.
        expanded = q.lower()  # Normalize to lowercase first
        
        # Academic title variations (only expand "dean of studies" to just "dean")
        expanded = expanded.replace("dean of studies", "dean")
        
        # Common abbreviations - expand 
        expanded = expanded.replace(" It ", " information technology ")
        expanded = expanded.replace(" IT", " information technology,")
        expanded = expanded.replace(" It.", " information technology.")
        expanded = expanded.replace(" Itohm", " Institute of Tourism and hospitality management")
        expanded = expanded.replace(" It ", " information technology ")
        expanded = expanded.replace(" IT", " information technology,")
        expanded = expanded.replace(" It.", " information technology.")
        expanded = expanded.replace(" It?", " information technology?")

        # Handle "and IT" specifically
        expanded = expanded.replace(" and it ", " and information technology ")
        expanded = expanded.replace(" & it ", " and information technology ")
        
        # CSIT expansion
        expanded = expanded.replace("csit", "computer science information technology")
        expanded = expanded.replace("cs & it", "computer science and information technology")
        expanded = expanded.replace("cs and it", "computer science and information technology")
        
        # School/Institute capitalization for better matching
        expanded = expanded.replace("school of", "school of")
        expanded = expanded.replace("institute of", "institute of")
        
        # For dean queries about specific schools, create a focused query
        # Extract: "dean" + school name keywords (remove location phrases)
        if "dean" in expanded:
            # Remove location phrases that dilute the signal
            expanded = re.sub(r'\s+in\s+dedan\s+kimathi.*', '', expanded, flags=re.IGNORECASE)
            expanded = re.sub(r'\s+at\s+dekut.*', '', expanded, flags=re.IGNORECASE)
            # Extract key terms: dean + school/institute name
            # Pattern: "dean [of] [the] [school/institute] [of] [school name]"
            dean_match = re.search(r'dean(?:\s+of)?(?:\s+the)?(?:\s+school|\s+institute)?(?:\s+of)?\s+([^?.,]+)', expanded)
            if dean_match:
                school_name = dean_match.group(1).strip()
                # Remove location phrases from school name too
                school_name = re.sub(r'\s+in\s+dedan.*', '', school_name, flags=re.IGNORECASE)
                # Create focused query: "dean [school name]"
                focused = f"dean {school_name}".strip()
                # If it's shorter and contains key terms, use it
                if len(focused) < len(expanded) and ("computer" in focused or "information" in focused):
                    expanded = focused
        
        return expanded

    expanded_query = expand_query(query)
    """
    search_query = "Represent this sentence for searching relevant passages: " + query
    docs = chroma_db.similarity_search_with_score(search_query, k=7)

    print("\n🔎 Retrieved Chunks:\n")

    relevant_docs = []
    threshold = 0.65  # tune this

    for i, (doc, score) in enumerate(docs):
     print(f"--- Chunk {i+1} | Score: {score:.4f} ---")
     print(doc.page_content[:400])
     print()

     if score <= threshold:
        relevant_docs.append(doc)

    if relevant_docs:
     context_text = "\n\n".join([f"###\n{doc.page_content}" for doc in relevant_docs])
     use_context = True
    else:
     use_context = False

    # --- 2. Build the final user prompt depending on whether we use context ---
    if use_context and context_text.strip():
        full_prompt = f"""You are DEKAI, an official assistant for Dedan Kimathi University of Technology (DeKUT).
Use ONLY the following context from DeKUT documents to answer the user's question accurately and helpfully.

CRITICAL RULES:
1. Use exact names, abbreviations, and titles from the context when available (e.g., "ICFoSS" not "ICSS").
2. If the context contains partial information (like a job title without full bio), still use it appropriately — do not ignore useful context.
3. If the answer clearly is not in the context at all, respond honestly and say you don't know.
4. Do NOT fabricate facts, staff names, program details, or links.
5. Only use `.dkut` in URLs and only if the link appears exactly in the context.
6. Prefer concise, factual responses. Use names, roles, and affiliations as they appear in the source.

Context:
{context_text}

User question: {query}

Grounded answer:"""

    else:
        # Non‑DeKUT or low-similarity queries: let the model use its own knowledge.
        full_prompt = query
    # 3. Convert to OpenRouter format
    history = serialize_history(db_messages)
    
    # 3. Add system prompt and the NEW prompt from the request
    system_prompt = """ 
    You are DEKAI, the official university assistant for Dedan Kimathi University of Technology (DeKUT).

    RULES:
    1. Respond to greetings such as "hello","hi","good morning","good afternoon" and any other conversation starter using your own knowledge.
    2. If the answer of a specific Dekut based question is not explicitly in the provided context, respond with: "I do not know. This information was not found in the available documents.""
    3. NEVER invent names, email addresses, URLs, or contact info.
    4. If a web link or email is not explicitly present in the context, do NOT guess it.
    5. Use abbreviations, department names, and titles exactly as written in the context.
    6. Keep answers concise and factual. Cite only what is grounded in retrieved content.

    If no context is provided, you may answer freely using your general knowledge — but never guess institutional details about DeKUT.
    """


    messages = [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": full_prompt},
    ]

    # 4. Call OpenRouter with error handling
    try:
        reply = openrouter.generate_openrouter_reply(messages)
    except RuntimeError as e:
        # Return user-friendly error message instead of crashing
        error_msg = str(e)
        logger.error(f"OpenRouter error: {error_msg}")
        return {
            "text": f"⚠️ {error_msg}\n\nPlease try again in a moment, or rephrase your question."
        }
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"Unexpected error in generation: {str(e)}", exc_info=True)
        return {
            "text": "⚠️ I encountered an error processing your request. Please try again or rephrase your question."
        }

    # 5. Clean the output: remove markdown formatting (asterisks, etc.)
    
    return {"text": reply}


@router.post("/conversation/{conversation_id}/generate-v1.5")
def generate_v15(
    conversation_id: int,
    request: schemas.GenerateRequest, # Use your request schema for user_input
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # 1. Verify ownership (standard check)
    conversation = db.query(models.Conversation).filter(
        models.Conversation.conversation_id == conversation_id,
        models.Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # 2. Call the new advanced model
    # We pass the user's latest input from the request
    reply = dekainlp15.generate_advanced_reply(request.prompt)
    

    return {"text": reply}