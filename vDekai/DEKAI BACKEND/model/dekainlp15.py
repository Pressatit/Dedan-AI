import numpy as np
import tensorflow as tf
import keras
from pathlib import Path
"""
# --- PERSISTENT LOADING ---
# Path to your local files
MODEL_PATH = Path("model/DEKAINLP1.5.keras")

print("Loading dekainlp1.5 into memory...")
model = keras.models.load_model(MODEL_PATH)

print("Model load complete!")

def standardize_keep_tokens(text):
    lower = tf.strings.lower(text)
    cleaned = tf.strings.regex_replace(lower, r"[^a-z0-9<> ]", "")
    cleaned = tf.strings.regex_replace(cleaned, r"\s+", " ")
    return cleaned

vectorizer = tf.keras.layers.TextVectorization(
    max_tokens=40000,
    output_mode="int",
    output_sequence_length=256,
    standardize=standardize_keep_tokens
)

with open("model/dekai_1.5_vocab", "r", encoding="utf-8") as f:
    raw_lines = [line.strip() for line in f.readlines()]
    
# Aligning the dictionary to prevent index shifts
clean_vocab = [word for word in raw_lines if not word.startswith("[source")]
vocab = clean_vocab[2:]

vectorizer.set_vocabulary(vocab)
print(vocab[:8])
# --------------------------

def generate_advanced_reply(user_input, temperature=0.7, repetition_penalty=1.2):
    
    Your Kaggle inference logic adapted for the persistent server.
    
    prompt = f"User: {user_input} Assistant:"
    
    # Accessing vectorizer (ensure it is loaded/defined in this scope)
    vocab = vectorizer.get_vocabulary()
    input_ids = vectorizer([prompt]).numpy()[0].tolist()
    input_ids = [t for t in input_ids if t != 0] 
    prompt_len = len(input_ids)
    
    PAD_ID, UNK_ID = 0, 1

    for _ in range(50):
        curr_len = len(input_ids)
        if curr_len >= 256: break 
            
        context = input_ids + [PAD_ID] * (256 - curr_len)
        preds = model(np.array([context], dtype=np.int32), training=False)
        logits = preds[0, curr_len - 1].numpy()
        
        # Repetition Penalty
        for token_id in set(input_ids[prompt_len:]):
            logits[token_id] /= repetition_penalty
            
        logits = logits / (temperature + 1e-8)
        logits[PAD_ID] -= 1e9
        logits[UNK_ID] -= 1e9
        
        probs = tf.nn.softmax(logits).numpy()
        next_id = np.random.choice(len(probs), p=probs)
        word = vocab[next_id]

        if word.lower() in ["user", "assistant"]:
            break
            
        input_ids.append(next_id)

    response_ids = input_ids[prompt_len:]
    return " ".join([vocab[i] for i in response_ids]).strip()
    """